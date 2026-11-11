"""Alocação de resgates por RDB, com custo e retenções calculados por operação.

A regra informada pelo Nubank compara (IR + IOF) por valor bruto. Como cada
resgate de um RDB aparece arredondado a centavos no extrato, a comparação é
recalculada após cada parcela, usando o valor que aquele lote efetivamente
poderia fornecer naquele momento.
"""

from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
HALF_CENT = Decimal("0.005")


@dataclass(frozen=True)
class WithdrawalAllocation:
    lot: object
    gross_amount: Decimal
    net_amount: Decimal
    principal_out: Decimal
    invested_out: Decimal
    yield_out: Decimal
    income_tax: Decimal
    iof: Decimal
    closed: bool

    @property
    def tax_ratio(self) -> Decimal:
        if self.gross_amount <= 0:
            return Decimal("Infinity")
        return (self.income_tax + self.iof) / self.gross_amount


def _cents_down(value: Decimal) -> Decimal:
    """Trunca retenções para centavos, conforme a composição observada no extrato."""
    return value.quantize(CENT, rounding=ROUND_DOWN)


def _cents_half_up(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def allocate_withdrawal(
    lots: list,
    net_amount: Decimal,
    day,
    sequence: int | None = None,
    *,
    strict: bool = True,
) -> list[WithdrawalAllocation]:
    """Aloca um saque líquido nos lotes elegíveis, com imposto arredondado por lote.

    Para comparar candidatos, estima a parcela necessária de cada lote. Se o
    lote não puder cobrir o saldo restante, considera seu resgate integral; se
    puder, encontra o menor bruto em centavos que cobre o líquido restante após
    IR e IOF truncados a centavos. Depois de cada resgate, recalcula as opções.
    """
    # Import local para evitar ciclo: tax_engine chama este módulo para simular
    # uma retirada e também é a fonte das regras fiscais e de elegibilidade.
    from app.services.tax_engine import (
        InsufficientBalanceError,
        gross_redemption_for_net,
        lock_is_active,
        redemption_taxes,
    )

    remaining = _cents_half_up(net_amount)
    allocations: list[WithdrawalAllocation] = []

    def tax_for(lot, gross: Decimal, *, full: bool):
        if full:
            principal_out = lot.principal
            invested_out = lot.invested
            yield_out = max(lot.value - lot.principal, Decimal("0"))
        else:
            fraction = gross / lot.value
            principal_out = lot.principal * fraction
            invested_out = lot.invested * fraction
            yield_out = max(gross - principal_out, Decimal("0"))
        ir_exact, iof_exact = redemption_taxes(yield_out, (day - lot.start).days)
        return (
            principal_out,
            invested_out,
            yield_out,
            _cents_down(ir_exact),
            _cents_down(iof_exact),
        )

    def candidate_for(lot) -> WithdrawalAllocation | None:
        if lot.value <= HALF_CENT:
            return None

        full_gross = _cents_half_up(lot.value)
        if full_gross <= 0:
            return None
        principal_out, invested_out, yield_out, ir, iof = tax_for(
            lot, lot.value, full=True
        )
        full_net = full_gross - ir - iof

        # Use a full redemption only when it does not overshoot the requested
        # net amount. A few cents left in an RDB are real; the statement can show
        # them being redeemed later, so do not silently erase them.
        if full_net <= remaining:
            return WithdrawalAllocation(
                lot=lot,
                gross_amount=full_gross,
                net_amount=full_net,
                principal_out=principal_out,
                invested_out=invested_out,
                yield_out=yield_out,
                income_tax=ir,
                iof=iof,
                closed=True,
            )

        age_days = (day - lot.start).days
        gross = _cents_down(
            gross_redemption_for_net(remaining, lot.value, lot.principal, age_days)
        )
        gross = max(gross, CENT)
        if gross >= lot.value:
            return WithdrawalAllocation(
                lot=lot,
                gross_amount=full_gross,
                net_amount=full_net,
                principal_out=lot.principal,
                invested_out=lot.invested,
                yield_out=max(lot.value - lot.principal, Decimal("0")),
                income_tax=ir,
                iof=iof,
                closed=True,
            )

        def partial(gross_amount: Decimal) -> WithdrawalAllocation:
            po, invested, yield_part, ir_part, iof_part = tax_for(
                lot, gross_amount, full=False
            )
            return WithdrawalAllocation(
                lot=lot,
                gross_amount=gross_amount,
                net_amount=gross_amount - ir_part - iof_part,
                principal_out=po,
                invested_out=invested,
                yield_out=yield_part,
                income_tax=ir_part,
                iof=iof_part,
                closed=False,
            )

        proposed = partial(gross)
        # The estimate uses unrounded tax ratios; adjust by cents to the smallest
        # gross that actually covers the remaining net after per-RDB rounding.
        while proposed.net_amount < remaining and gross < full_gross:
            gross += CENT
            proposed = partial(gross)
        while gross > CENT:
            smaller = partial(gross - CENT)
            if smaller.net_amount < remaining:
                break
            gross -= CENT
            proposed = smaller
        return proposed

    while remaining > HALF_CENT:
        eligible = [
            lot
            for lot in lots
            if lot.start <= day
            and not lock_is_active(lot, day)
            and not (
                sequence is not None
                and lot.start == day
                and lot.sequence > sequence
            )
        ]
        options = []
        for lot in eligible:
            candidate = candidate_for(lot)
            if candidate is not None:
                # Re-evaluate the effective tax cost of the actual contribution.
                # On equal costs, keep the deterministic preference for larger lots.
                options.append(
                    (
                        candidate.tax_ratio,
                        -lot.value,
                        -lot.start.toordinal(),
                        -lot.sequence,
                        candidate,
                    )
                )
        if not options:
            if not strict:
                break
            locked_amount = sum(
                (lot.value for lot in lots if lock_is_active(lot, day)),
                Decimal("0"),
            )
            raise InsufficientBalanceError(day, remaining, locked_amount)

        allocation = min(options, key=lambda option: option[:4])[4]
        lot = allocation.lot
        allocations.append(allocation)
        remaining = _cents_half_up(max(Decimal("0"), remaining - allocation.net_amount))

        if allocation.closed:
            lot.value = Decimal("0")
            lot.principal = Decimal("0")
            lot.invested = Decimal("0")
        else:
            lot.value -= allocation.gross_amount
            lot.principal -= allocation.principal_out
            lot.invested -= allocation.invested_out

    if strict and remaining > HALF_CENT:
        locked_amount = sum(
            (lot.value for lot in lots if lock_is_active(lot, day)), Decimal("0")
        )
        raise InsufficientBalanceError(day, remaining, locked_amount)

    lots[:] = [lot for lot in lots if lot.value > HALF_CENT]
    return allocations
