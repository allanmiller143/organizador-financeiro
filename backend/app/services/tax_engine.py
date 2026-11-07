from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.services.yield_engine import Flow, check_coverage, daily_yield_rate

CENT_TOLERANCE = Decimal("0.005")  # meio centavo: absorve diferenças de arredondamento


class InsufficientBalanceError(Exception):
    """A retirada é maior que o saldo da caixinha naquele dia."""

    def __init__(self, day: date, shortfall: Decimal):
        super().__init__(f"Saldo insuficiente em {day}: faltam {shortfall}")
        self.day = day
        self.shortfall = shortfall


@dataclass
class Lot:
    """Um aporte: a data em que entrou, o valor aportado e o valor atual."""

    start: date
    principal: Decimal
    value: Decimal


@dataclass(frozen=True)
class TaxSummary:
    gross_balance: Decimal  # saldo bruto
    invested: Decimal  # parte do saldo que é dinheiro aportado
    gross_yield: Decimal  # rendimento ainda dentro da caixinha
    tax_estimated: Decimal  # IR se resgatasse tudo na data final
    net_balance: Decimal  # saldo bruto menos o IR estimado
    tax_paid: Decimal  # IR já retido nas retiradas feitas


def ir_rate(age_days: int) -> Decimal:
    """Alíquota regressiva do IR conforme os dias corridos desde o aporte."""
    if age_days <= 180:
        return Decimal("0.225")
    if age_days <= 360:
        return Decimal("0.20")
    if age_days <= 720:
        return Decimal("0.175")
    return Decimal("0.15")


def _withdraw(lots: list[Lot], amount: Decimal, day: date) -> Decimal:
    """Retira dos lotes mais antigos primeiro e devolve o IR retido."""
    remaining = amount
    tax = Decimal("0")
    for lot in lots:
        if remaining <= CENT_TOLERANCE:
            break
        take = min(remaining, lot.value)
        principal_out = lot.principal * (take / lot.value)
        yield_out = take - principal_out
        tax += yield_out * ir_rate((day - lot.start).days)
        lot.principal -= principal_out
        lot.value -= take
        remaining -= take

    if remaining > CENT_TOLERANCE:
        raise InsufficientBalanceError(day, remaining)

    lots[:] = [lot for lot in lots if lot.value > CENT_TOLERANCE]  # descarta lotes zerados
    return tax


def simulate_lots(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
) -> TaxSummary:
    """Percorre os dias de start a end com lotes e devolve o resumo com imposto."""
    check_coverage(rates, start, end)

    deposits: dict[date, Decimal] = defaultdict(Decimal)
    withdrawals: dict[date, Decimal] = defaultdict(Decimal)
    for flow in flows:
        if flow.amount >= 0:
            deposits[flow.day] += flow.amount
        else:
            withdrawals[flow.day] += -flow.amount

    lots: list[Lot] = []
    tax_paid = Decimal("0")
    day = start
    while day <= end:
        if day in rates:  # dia útil: todos os lotes rendem
            factor = 1 + daily_yield_rate(rates[day], cdi_percent)
            for lot in lots:
                lot.value *= factor
        if day in deposits:
            lots.append(Lot(start=day, principal=deposits[day], value=deposits[day]))
        if day in withdrawals:
            tax_paid += _withdraw(lots, withdrawals[day], day)
        day += timedelta(days=1)

    gross = sum((lot.value for lot in lots), Decimal("0"))
    invested = sum((lot.principal for lot in lots), Decimal("0"))
    estimated = sum(
        ((lot.value - lot.principal) * ir_rate((end - lot.start).days) for lot in lots),
        Decimal("0"),
    )
    return TaxSummary(
        gross_balance=gross,
        invested=invested,
        gross_yield=gross - invested,
        tax_estimated=estimated,
        net_balance=gross - estimated,
        tax_paid=tax_paid,
    )