import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal

from flask import current_app
from sqlalchemy import func, select

from app.errors import AppError
from app.extensions import db
from app.models import Account, CdiRate, Transaction, TransactionKind
from app.services import account_service, cdi_service
from app.services.tax_engine import InsufficientBalanceError, TaxSummary, simulate_lots
from app.services.yield_engine import (
    CdiCoverageError,
    Flow,
    monthly_yields,
    simulate,
    to_cents,
)


@dataclass
class _Context:
    account: Account
    flows: list[Flow]
    rates: dict[date, Decimal]
    start: date
    end: date


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
        .order_by(Transaction.occurred_on)
    )
    return [
        Flow(t.occurred_on, t.amount if t.kind == TransactionKind.DEPOSIT else -t.amount)
        for t in transactions
    ]


def _load_rates(start: date, end: date) -> dict[date, Decimal]:
    rows = db.session.execute(
        select(CdiRate.reference_date, CdiRate.daily_rate).where(
            CdiRate.reference_date >= start, CdiRate.reference_date <= end
        )
    )
    return {day: rate for day, rate in rows}


def _build_context(account: Account) -> _Context | None:
    """Reúne o que os motores precisam. Devolve None se não há CDI no banco."""
    all_flows = _load_flows(account)
    if all_flows:
        cdi_service.ensure_covers(all_flows[0].day)  # baixa o CDI que faltar

    last_cdi = db.session.scalar(select(func.max(CdiRate.reference_date)))
    if last_cdi is None:
        return None

    end = min(date.today(), last_cdi)
    flows = [flow for flow in all_flows if flow.day <= end]
    start = flows[0].day if flows else end
    return _Context(account, flows, _load_rates(start, end), start, end)


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
        raise AppError(
            f"Essa operação deixaria o saldo negativo em {exc.day:%d/%m/%Y}.",
            422,
            "withdrawal_exceeds_balance",
        ) from exc
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
    return {"account_id": ctx.account.id, "as_of": ctx.end, **values}


def account_monthly_yields(user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
    ctx = _prepare(user_id, account_id)
    with _engine_errors():
        points = simulate(
            ctx.flows, ctx.rates, ctx.account.cdi_percent, ctx.start, ctx.end
        )
    months = [
        {"month": month, "yield_amount": to_cents(value)}
        for month, value in monthly_yields(points)
    ]
    return {"account_id": ctx.account.id, "as_of": ctx.end, "months": months}


def dashboard(user_id: uuid.UUID) -> dict:
    cdi_service.ensure_fresh()

    results = []
    for account in account_service.list_accounts(user_id):
        ctx = _build_context(account)
        if ctx is None:
            raise AppError("O CDI ainda não foi sincronizado.", 409, "cdi_not_synced")
        with _engine_errors():
            summary = simulate_lots(
                ctx.flows, ctx.rates, account.cdi_percent, ctx.start, ctx.end
            )
        results.append((account, ctx.end, summary))

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