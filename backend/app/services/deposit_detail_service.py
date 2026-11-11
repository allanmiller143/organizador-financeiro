from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.services.tax_engine import (
    Lot,
    ir_rate,
    lock_end_date,
    lock_is_active,
    rate_percent,
    redemption_taxes,
    rollover_due_date,
)
from app.services.yield_engine import Flow, check_coverage, daily_yield_rate

PRODUCT_IMMEDIATE = "RDB Resgate Imediato"
PRODUCT_PLANNED = "RDB Planejado"
CENT = Decimal("0.005")


@dataclass
class DepositDetailState:
    lot: Lot
    deposited: Decimal
    withdrawn: Decimal = Decimal("0")
    yield_withdrawn: Decimal = Decimal("0")  # rendimento que já saiu em retiradas
    ir_paid: Decimal = Decimal("0")
    iof_paid: Decimal = Decimal("0")
    withdrawals: list[dict] = field(default_factory=list)  # um item por resgate


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _new_state(flow: Flow) -> DepositDetailState:
    return DepositDetailState(
        lot=Lot(
            flow.day,
            flow.amount,
            flow.amount,
            flow.amount,
            flow.cdi_percent,
            flow.term_months,
            flow.locked,
            flow.sequence,
            flow.source_id,
            flow.reinvestment_order,
        ),
        deposited=flow.amount,
    )


def _withdraw_from_states(
    states: list[DepositDetailState], flow: Flow, day: date
) -> list[DepositDetailState]:
    """Aplica ao detalhamento as mesmas parcelas usadas no motor agregado."""
    from app.services.withdrawal_allocator import allocate_withdrawal

    state_by_lot = {id(state.lot): state for state in states}
    allocations = allocate_withdrawal(
        [state.lot for state in states],
        -flow.amount,
        day,
        flow.sequence,
        strict=False,
    )
    for allocation in allocations:
        state = state_by_lot[id(allocation.lot)]
        state.withdrawn += allocation.net_amount
        state.yield_withdrawn += allocation.yield_out
        state.ir_paid += allocation.income_tax
        state.iof_paid += allocation.iof
        state.withdrawals.append(
            {
                "occurred_on": day,
                "amount": _money(allocation.net_amount),
                "gross_amount": _money(allocation.gross_amount),
                "gross_yield": _money(allocation.yield_out),
                "income_tax": _money(allocation.income_tax),
                "iof": _money(allocation.iof),
                "net_amount": _money(allocation.net_amount),
            }
        )
    return [state for state in states if state.lot.value > CENT]


def calculate_deposit_details(
    flows: list[Flow], rates: dict[date, Decimal], base_percent: Decimal, start: date, end: date
) -> list[dict]:
    """Um item por lote (depósito) ainda existente, com rendimento, IR e IOF por resgate."""
    check_coverage(rates, start, end)
    by_day: dict[date, list[Flow]] = {}
    for flow in flows:
        by_day.setdefault(flow.day, []).append(flow)
    for values in by_day.values():
        values.sort(key=lambda flow: flow.sequence)

    states: list[DepositDetailState] = []
    all_states: list[DepositDetailState] = []
    day = start
    while day <= end:
        for flow in by_day.get(day, []):
            if flow.amount >= 0:
                new_state = _new_state(flow)
                states.append(new_state)
                all_states.append(new_state)

        # O resgate é fechado antes do crédito do CDI do dia. O aporte ainda
        # fica disponível para o resgate do próprio dia, mas o valor retirado
        # não recebe o rendimento desse dia.
        for flow in by_day.get(day, []):
            if flow.amount < 0:
                states = _withdraw_from_states(states, flow, day)

        # Rendimento em dia útil, inclusive no próprio dia do depósito, apenas
        # sobre o saldo que permaneceu depois dos resgates.
        if day in rates:
            for state in states:
                state.lot.value *= 1 + daily_yield_rate(
                    rates[day], rate_percent(state.lot, day, base_percent)
                )

        # Vencimento: o lote original sai e nasce um novo lote Resgate Imediato.
        due_states = []
        for state in states:
            due_date = (
                lock_end_date(state.lot.start, state.lot.term_months)
                if state.lot.locked
                else rollover_due_date(state.lot.start)
            )
            if day >= due_date:
                due_states.append(state)
        due_states.sort(
            key=lambda state: (
                state.lot.reinvestment_order
                if state.lot.reinvestment_order is not None
                else state.lot.sequence,
                state.lot.sequence,
            )
        )
        for state in due_states:
            states.remove(state)
            tax_base = max(state.lot.value - state.lot.principal, Decimal("0"))
            tax = _money(tax_base * ir_rate((day - state.lot.start).days))
            reinvested = _money(state.lot.value - tax)
            state.lot.value = Decimal("0")
            state.lot.principal = Decimal("0")
            state.lot.invested = Decimal("0")
            if reinvested > CENT:
                replacement = DepositDetailState(
                    lot=Lot(
                        day,
                        reinvested,
                        reinvested,
                        reinvested,
                        base_percent,
                        24,
                        False,
                        state.lot.sequence,
                        state.lot.source_id,
                        state.lot.reinvestment_order,
                    ),
                    deposited=reinvested,
                )
                states.append(replacement)
                all_states.append(replacement)

        day += timedelta(days=1)

    result = []
    for state in all_states:
        lot = state.lot
        # Lotes zerados (resgatados por inteiro ou reaplicados) saem da lista.
        if lot.value <= CENT:
            continue
        age = (end - lot.start).days
        current_yield = max(lot.value - lot.principal, Decimal("0"))
        estimated_ir, estimated_iof = redemption_taxes(current_yield, age)
        result.append(
            {
                "deposited_on": lot.start,
                "product": PRODUCT_PLANNED if lot.locked else PRODUCT_IMMEDIATE,
                "applied_amount": _money(state.deposited),
                "principal_remaining": _money(lot.principal),
                "partial_withdrawals": _money(state.withdrawn),
                "gross_yield": _money(current_yield + state.yield_withdrawn),  # rendimento total do depósito
                "income_tax": _money(state.ir_paid + estimated_ir),
                "iof": _money(state.iof_paid),  # IOF efetivamente cobrado em resgates
                "iof_estimated": _money(estimated_iof),  # IOF se o restante fosse resgatado hoje
                "gross_balance": _money(lot.value),
                "net_balance": _money(lot.value - estimated_ir - estimated_iof),
                "maturity_on": lock_end_date(lot.start, lot.term_months)
                if lot.locked
                else rollover_due_date(lot.start),
                "locked": lock_is_active(lot, end),
                "term_months": lot.term_months,
                "cdi_percent": lot.cdi_percent,
                "withdrawals": state.withdrawals,
                # Campo interno usado somente para ordenar aportes do mesmo dia.
                "_sequence": lot.sequence,
            }
        )
    # A ordem dos aportes no mesmo dia faz parte do histórico: não ordenar pelo valor.
    result.sort(key=lambda item: (item["deposited_on"], item["_sequence"]))
    for item in result:
        item.pop("_sequence", None)
    return result
