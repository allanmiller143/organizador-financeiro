import csv
import io
import math
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from datetime import date, timedelta
from decimal import Decimal

from flask import current_app
from sqlalchemy import func, select

from app.errors import AppError
from app.extensions import db
from app.models import Account, CdiRate, Transaction, TransactionKind
from app.services import account_service, cdi_service
from app.services.calendar_br import today_brazil
from app.services.deposit_detail_service import calculate_deposit_details
from app.services.tax_engine import (
    InsufficientBalanceError,
    TaxSummary,
    monthly_lot_balances,
    simulate_lots,
)
from app.services.yield_engine import (
    CdiCoverageError,
    Flow,
    to_cents,
)


@dataclass
class _Context:
    account: Account
    flows: list[Flow]
    rates: dict[date, Decimal]
    start: date
    end: date
    as_of: date


@contextmanager
def _engine_errors():
    """Converte os erros dos motores em erros de API com mensagem clara."""
    try:
        yield
    except CdiCoverageError as exc:
        raise AppError(
            "Faltam dados do CDI para o período desta caixinha.", 409, "cdi_incomplete"
        ) from exc
    except InsufficientBalanceError as exc:
        raise AppError(
            f"Há uma retirada maior que o saldo em {exc.day:%d/%m/%Y}.",
            409,
            "insufficient_balance",
        ) from exc


def _load_flows(account: Account) -> list[Flow]:
    transactions = db.session.scalars(
        select(Transaction)
        .where(Transaction.account_id == account.id)
        .order_by(
            Transaction.occurred_on,
            Transaction.sort_order.asc().nullslast(),
            Transaction.id.desc(),
        )
    )
    ordered_transactions = list(transactions)
    day_positions: dict[date, int] = {}
    flows = []
    for t in ordered_transactions:
        position = day_positions.get(t.occurred_on, 0)
        day_positions[t.occurred_on] = position + 1
        is_deposit = t.kind == TransactionKind.DEPOSIT
        # Só aporte em caixinha de 100% pode ser trancado. Aporte normal rende o padrão
        # da caixinha, não importa o % gravado nele (dados antigos podem estar errados).
        locked = is_deposit and t.locked and account.cdi_percent <= 100
        flows.append(
            Flow(
                t.occurred_on,
                t.amount if is_deposit else -t.amount,
                t.cdi_percent if locked else account.cdi_percent,
                t.term_months if locked else 24,
                locked,
                # O motor precisa da posição relativa no próprio dia. O
                # sort_order antigo pode ser global ou ter sido criado antes
                # de uma reordenação; usar a posição da consulta evita que um
                # aporte posterior receba uma retirada anterior.
                position,
                str(t.id),
                t.reinvestment_order,
            )
        )
    return flows


def _load_rates(start: date, end: date) -> dict[date, Decimal]:
    rows = db.session.execute(
        select(CdiRate.reference_date, CdiRate.daily_rate).where(
            CdiRate.reference_date >= start, CdiRate.reference_date <= end
        )
    )
    return {day: rate for day, rate in rows}


def _build_context(account: Account) -> _Context | None:
    """Reúne o que os motores precisam. Devolve None se não há CDI no banco."""
    cdi_service.ensure_fresh()
    all_flows = _load_flows(account)
    if all_flows:
        cdi_service.ensure_covers(all_flows[0].day)  # baixa o CDI que faltar

    last_cdi = db.session.scalar(select(func.max(CdiRate.reference_date)))
    if last_cdi is None:
        return None

    today = today_brazil()
    # O saldo contabiliza movimentações já lançadas mesmo quando o CDI mais
    # recente ainda é de um dia anterior. Dias sem uma taxa publicada não
    # recebem rendimento; `as_of` continua indicando a data real do CDI usado.
    eligible_flows = [flow for flow in all_flows if flow.day <= today]
    latest_flow_day = max((flow.day for flow in eligible_flows), default=last_cdi)
    end = max(last_cdi, latest_flow_day)
    # Mantém a data civil atual mesmo em dia útil sem CDI publicado ainda. Isso
    # avança idade tributária e permite maturidades/reaplicações, sem inventar
    # rendimento nos dias que não têm taxa gravada.
    if today >= last_cdi and today - last_cdi <= timedelta(days=5):
        end = max(end, today)
    flows = [flow for flow in all_flows if flow.day <= end]
    start = flows[0].day if flows else end
    # Inclui a última taxa conhecida mesmo que o primeiro fluxo seja mais novo;
    # isso permite validar saldo principal sem exigir CDI no dia do aporte.
    rates_start = min(start, last_cdi)
    return _Context(account, flows, _load_rates(rates_start, end), start, end, last_cdi)


def _prepare(user_id: uuid.UUID, account_id: uuid.UUID) -> _Context:
    account = account_service.get_account(user_id, account_id)
    ctx = _build_context(account)
    if ctx is None:
        raise AppError("O CDI ainda não foi sincronizado.", 409, "cdi_not_synced")
    return ctx


def ensure_consistent_history(account: Account) -> None:
    """Levanta AppError se alguma retirada ficar maior que o saldo do dia.

    Só valida se há CDI cobrindo o período; sem ele, deixa passar e avisa no log.
    """
    ctx = _build_context(account)
    if ctx is None or not ctx.flows:
        return
    try:
        simulate_lots(ctx.flows, ctx.rates, account.cdi_percent, ctx.start, ctx.end)
    except InsufficientBalanceError as exc:
        message = f"Essa operação deixaria o saldo negativo em {exc.day:%d/%m/%Y}."
        if exc.locked_amount > 0:
            locked = f"{to_cents(exc.locked_amount):,.2f}".replace(",", "X").replace(".", ",")
            message = (
                f"Saldo disponível insuficiente em {exc.day:%d/%m/%Y}: "
                f"R$ {locked.replace('X', '.')} estão trancados até o fim do prazo."
            )
        raise AppError(message, 422, "withdrawal_exceeds_balance") from exc
    except CdiCoverageError:
        current_app.logger.warning(
            "CDI incompleto: histórico da caixinha %s não foi validado", account.id
        )


def account_summary(user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
    ctx = _prepare(user_id, account_id)
    with _engine_errors():
        summary = simulate_lots(
            ctx.flows, ctx.rates, ctx.account.cdi_percent, ctx.start, ctx.end
        )
    values = {name: to_cents(value) for name, value in asdict(summary).items()}
    return {"account_id": ctx.account.id, "as_of": ctx.as_of, **values}



FORECAST_HORIZON_DAYS = 365 * 30  # limite da busca: 30 anos


def _months_between(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + end.month - start.month
    if end.day > start.day:
        months += 1
    return max(1, months)


def account_goal_forecast(user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
    """Estima o prazo da meta pelo saldo LÍQUIDO, simulando o motor tributário.

    Projeta o CDI médio recente em dias úteis futuros, sem novos aportes/retiradas,
    e procura (busca binária) o primeiro dia em que o saldo líquido atinge a meta.
    """
    account = account_service.get_account(user_id, account_id)
    if account.goal_amount is None:
        raise AppError("Defina uma meta para estimar o prazo.", 409, "goal_not_set")

    goal = account.goal_amount
    today = today_brazil()
    ctx = _prepare(user_id, account_id)

    with _engine_errors():
        current = simulate_lots(
            ctx.flows, ctx.rates, account.cdi_percent, ctx.start, ctx.end
        )
    balance = to_cents(current.net_balance)

    base = {"balance": balance, "goal_amount": goal}

    if balance >= goal:
        return {
            **base,
            "status": "reached",
            "months": 0,
            "projected_date": today,
            "assumption": "Saldo líquido (após impostos estimados) já atingiu a meta.",
        }
    if balance <= 0:
        return {
            **base,
            "status": "no_balance",
            "months": None,
            "projected_date": None,
            "assumption": "Sem saldo atual, não há prazo estimável sem novos aportes.",
        }

    rows = db.session.scalars(
        select(CdiRate)
        .where(CdiRate.reference_date >= today - timedelta(days=60))
        .order_by(CdiRate.reference_date.desc())
        .limit(30)
    )
    recent_rates = [row.daily_rate for row in rows]
    if not recent_rates:
        raise AppError("Não há histórico recente de CDI para estimar a meta.", 409, "cdi_not_synced")

    average_daily_rate = sum(recent_rates, Decimal("0")) / len(recent_rates)
    no_growth = {
        **base,
        "status": "no_growth",
        "months": None,
        "projected_date": None,
        "assumption": "Sem crescimento positivo estimável em até 30 anos com o CDI recente.",
    }
    if average_daily_rate <= 0:
        return no_growth

    # Taxas futuras: média recente em todos os dias úteis (seg-sex) após o último dia simulado.
    horizon_end = ctx.end + timedelta(days=FORECAST_HORIZON_DAYS)
    future_rates = dict(ctx.rates)
    day = ctx.end + timedelta(days=1)
    while day <= horizon_end:
        if day.weekday() < 5:
            future_rates[day] = average_daily_rate
        day += timedelta(days=1)

    def net_at(target: date) -> Decimal:
        return simulate_lots(
            ctx.flows, future_rates, account.cdi_percent, ctx.start, target
        ).net_balance

    with _engine_errors():
        if net_at(horizon_end) < goal:
            return no_growth
        low, high = ctx.end, horizon_end  # low: abaixo da meta; high: atinge a meta
        while (high - low).days > 1:
            mid = low + (high - low) // 2
            if net_at(mid) >= goal:
                high = mid
            else:
                low = mid

    return {
        **base,
        "status": "projected",
        "months": _months_between(today, high),
        "projected_date": high,
        "assumption": (
            "Saldo líquido (após IR e IOF estimados). Média dos últimos até 30 registros "
            "de CDI mantida nos dias úteis; sem novos aportes/retiradas."
        ),
    }


def account_monthly_yields(user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
    ctx = _prepare(user_id, account_id)
    with _engine_errors():
        balances = monthly_lot_balances(
            ctx.flows, ctx.rates, ctx.account.cdi_percent, ctx.start, ctx.end
        )
    # Net yield includes taxes accrued during the month and taxes paid on withdrawals.
    previous_estimated_tax = Decimal("0")
    previous_paid_tax = Decimal("0")
    months = []
    for balance in balances:
        yield_amount = balance.yield_amount
        net_yield_amount = yield_amount - (
            balance.tax_estimated - previous_estimated_tax
        ) - (balance.tax_paid - previous_paid_tax)
        months.append(
            {
                "month": balance.month,
                "yield_amount": to_cents(yield_amount),
                "net_yield_amount": to_cents(net_yield_amount),
                "gross_balance": to_cents(balance.gross_balance),
                "net_balance": to_cents(balance.net_balance),
                "invested": to_cents(balance.invested),
                "reapplications": [
                    {
                        "occurred_on": event.occurred_on,
                        "gross_yield": to_cents(event.gross_yield),
                        "tax_paid": event.tax_paid,
                        "amount": event.amount,
                        "source_transaction_id": event.source_transaction_id,
                    }
                    for event in balance.reapplications
                ],
            }
        )
        previous_estimated_tax = balance.tax_estimated
        previous_paid_tax = balance.tax_paid
    return {"account_id": ctx.account.id, "as_of": ctx.as_of, "months": months}


def account_deposit_details(user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
    ctx = _prepare(user_id, account_id)
    with _engine_errors():
        deposits = calculate_deposit_details(
            ctx.flows, ctx.rates, ctx.account.cdi_percent, ctx.start, ctx.end
        )
    return {"account_id": ctx.account.id, "as_of": ctx.as_of, "deposits": deposits}


def account_deposit_details_csv(user_id: uuid.UUID, account_id: uuid.UUID) -> str:
    """Exporta os lotes atuais com rendimento, tributos e saques alocados."""
    data = account_deposit_details(user_id, account_id)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["tipo", "data_lote", "data_evento", "aplicado", "saque", "rendimento_bruto", "ir", "iof_pago", "iof_estimado", "saldo_bruto", "saldo_liquido", "produto"])
    for deposit in data["deposits"]:
        writer.writerow(["LOTE", deposit["deposited_on"].isoformat(), "", deposit["applied_amount"], deposit["partial_withdrawals"], deposit["gross_yield"], deposit["income_tax"], deposit["iof"], deposit["iof_estimated"], deposit["gross_balance"], deposit["net_balance"], deposit["product"]])
        for withdrawal in deposit["withdrawals"]:
            writer.writerow(["SAQUE_ALOCADO", deposit["deposited_on"].isoformat(), withdrawal["occurred_on"].isoformat(), "", withdrawal["amount"], withdrawal["gross_yield"], withdrawal["income_tax"], withdrawal["iof"], "", "", withdrawal["net_amount"], deposit["product"]])
    return "\ufeff" + output.getvalue()


def account_history_csv(user_id: uuid.UUID, account_id: uuid.UUID) -> str:
    """Exporta o histórico simples, incluindo reaplicações geradas pelo vencimento."""
    ctx = _prepare(user_id, account_id)
    with _engine_errors():
        balances = monthly_lot_balances(
            ctx.flows, ctx.rates, ctx.account.cdi_percent, ctx.start, ctx.end
        )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["dia", "operacao", "valor"])
    rows = [
        (flow.day, flow.sequence, "aporte" if flow.amount > 0 else "retirada", abs(flow.amount))
        for flow in ctx.flows
    ]
    for month_index, balance in enumerate(balances):
        for event_index, event in enumerate(balance.reapplications):
            # Eventos de reaplicação são criados pelo motor; não são novos
            # lançamentos cadastrados pelo usuário e não devem ser inferidos
            # a partir de reinvestment_order do aporte original.
            rows.append((event.occurred_on, 1_000_000 + month_index * 10_000 + event_index, "reinvestimento", event.amount))
    for day, sequence, operation, amount in sorted(
        rows, key=lambda item: (-item[0].toordinal(), item[1])
    ):
        writer.writerow([day.isoformat(), operation, amount])
    return "\ufeff" + output.getvalue()


def dashboard(user_id: uuid.UUID) -> dict:
    cdi_service.ensure_fresh()

    results = []
    active_accounts = [a for a in account_service.list_accounts(user_id) if a.is_active]
    for account in active_accounts:
        ctx = _build_context(account)
        if ctx is None:
            raise AppError("O CDI ainda não foi sincronizado.", 409, "cdi_not_synced")
        with _engine_errors():
            summary = simulate_lots(
                ctx.flows, ctx.rates, account.cdi_percent, ctx.start, ctx.end
            )
        results.append((account, ctx.as_of, summary))

    names = [field.name for field in fields(TaxSummary)]
    totals = {
        name: sum((getattr(summary, name) for _, _, summary in results), Decimal("0"))
        for name in names
    }
    total_gross = totals["gross_balance"]

    accounts = []
    for account, _, summary in results:
        share = summary.gross_balance / total_gross * 100 if total_gross > 0 else Decimal("0")
        accounts.append(
            {
                "account_id": account.id,
                "name": account.name,
                "institution": account.institution,
                "goal_amount": account.goal_amount,
                "share_percent": to_cents(share),
                "gross_balance": to_cents(summary.gross_balance),
                "net_balance": to_cents(summary.net_balance),
                "gross_yield": to_cents(summary.gross_yield),
            }
        )

    return {
        "as_of": max((end for _, end, _ in results), default=None),
        "totals": {name: to_cents(value) for name, value in totals.items()},
        "accounts": accounts,
    }
