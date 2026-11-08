from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.services.yield_engine import Flow, check_coverage, daily_yield_rate

CENT_TOLERANCE = Decimal("0.005")  # meio centavo: absorve diferenças de arredondamento
IR_LOWEST_RATE_AGE_DAYS = 720
ROLLOVER_AGE_MONTHS = 24


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
    invested: Decimal


@dataclass(frozen=True)
class TaxSummary:
    gross_balance: Decimal  # saldo bruto
    invested: Decimal  # parte do saldo que é dinheiro aportado
    gross_yield: Decimal  # rendimento ainda dentro da caixinha
    tax_estimated: Decimal  # IR se resgatasse tudo na data final
    net_balance: Decimal  # saldo bruto menos o IR estimado
    tax_paid: Decimal  # IR já retido nas retiradas feitas


@dataclass(frozen=True)
class Reinvestment:
    occurred_on: date
    gross_yield: Decimal
    tax_paid: Decimal
    amount: Decimal


@dataclass(frozen=True)
class MonthlyBalance:
    month: str
    yield_amount: Decimal
    gross_balance: Decimal
    net_balance: Decimal
    tax_estimated: Decimal
    tax_paid: Decimal
    reapplications: list[Reinvestment]


def ir_rate(age_days: int) -> Decimal:
    """Alíquota regressiva do IR conforme os dias corridos desde o aporte."""
    if age_days <= 180:
        return Decimal("0.225")
    if age_days <= 360:
        return Decimal("0.20")
    if age_days < IR_LOWEST_RATE_AGE_DAYS:
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
        invested_out = lot.invested * (take / lot.value)
        yield_out = take - principal_out
        tax += yield_out * ir_rate((day - lot.start).days)
        lot.principal -= principal_out
        lot.invested -= invested_out
        lot.value -= take
        remaining -= take

    if remaining > CENT_TOLERANCE:
        raise InsufficientBalanceError(day, remaining)

    lots[:] = [lot for lot in lots if lot.value > CENT_TOLERANCE]  # descarta lotes zerados
    return tax


def rollover_due_date(start: date) -> date:
    """Devolve o aniversário de dois anos, limitando dias inexistentes ao fim do mês."""
    year = start.year + 2
    day = min(start.day, monthrange(year, start.month)[1])
    return date(year, start.month, day)


def settle_matured_lot(principal: Decimal, value: Decimal) -> tuple[Decimal, Decimal]:
    """Calcula o IR do vencimento e o valor líquido a reinvestir."""
    taxable_yield = max(value - principal, Decimal("0"))
    tax = (taxable_yield * ir_rate(IR_LOWEST_RATE_AGE_DAYS)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    reinvested = (value - tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return tax, reinvested


def _rollover_matured_lots(lots: list[Lot], day: date) -> tuple[Decimal, list[Reinvestment]]:
    """Reinveste cada lote na data de dois anos, descontando IR do rendimento acumulado."""
    tax_paid = Decimal("0")
    reapplications = []
    remaining_lots = []
    for lot in lots:
        if day < rollover_due_date(lot.start):
            remaining_lots.append(lot)
            continue

        tax, reinvested = settle_matured_lot(lot.principal, lot.value)
        tax_paid += tax
        reapplications.append(
            Reinvestment(
                occurred_on=day,
                gross_yield=lot.value - lot.principal,
                tax_paid=tax,
                amount=reinvested,
            )
        )
        if reinvested > CENT_TOLERANCE:
            remaining_lots.append(
                Lot(
                    start=day,
                    principal=reinvested,
                    value=reinvested,
                    invested=lot.invested,
                )
            )

    lots[:] = remaining_lots
    return tax_paid, reapplications


def _summarize_lots(lots: list[Lot], day: date, tax_paid: Decimal) -> TaxSummary:
    gross = sum((lot.value for lot in lots), Decimal("0"))
    invested = sum((lot.invested for lot in lots), Decimal("0"))
    estimated = sum(
        ((lot.value - lot.principal) * ir_rate((day - lot.start).days) for lot in lots),
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


def _simulate_lots(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
    include_monthly_balances: bool,
) -> tuple[TaxSummary, list[MonthlyBalance]]:
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
    monthly_balances: list[MonthlyBalance] = []
    monthly_yields: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
    monthly_reapplications: dict[tuple[int, int], list[Reinvestment]] = defaultdict(list)
    day = start
    while day <= end:
        earned = Decimal("0")
        if day in rates:  # dia útil: todos os lotes rendem
            rate = daily_yield_rate(rates[day], cdi_percent)
            for lot in lots:
                earned += lot.value * rate
                lot.value *= 1 + rate
        monthly_yields[(day.year, day.month)] += earned
        if day in deposits:
            lots.append(
                Lot(
                    start=day,
                    principal=deposits[day],
                    value=deposits[day],
                    invested=deposits[day],
                )
            )
        if day in withdrawals:
            tax_paid += _withdraw(lots, withdrawals[day], day)
        rollover_tax, reapplications = _rollover_matured_lots(lots, day)
        tax_paid += rollover_tax
        monthly_reapplications[(day.year, day.month)].extend(reapplications)
        if include_monthly_balances and (
            day == end or day.month != (day + timedelta(days=1)).month
        ):
            summary = _summarize_lots(lots, day, tax_paid)
            monthly_balances.append(
                MonthlyBalance(
                    month=f"{day.year}-{day.month:02d}",
                    yield_amount=monthly_yields[(day.year, day.month)],
                    gross_balance=summary.gross_balance,
                    net_balance=summary.net_balance,
                    tax_estimated=summary.tax_estimated,
                    tax_paid=summary.tax_paid,
                    reapplications=monthly_reapplications[(day.year, day.month)],
                )
            )
        day += timedelta(days=1)

    return _summarize_lots(lots, end, tax_paid), monthly_balances


def simulate_lots(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
) -> TaxSummary:
    return _simulate_lots(flows, rates, cdi_percent, start, end, False)[0]


def monthly_lot_balances(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
) -> list[MonthlyBalance]:
    return _simulate_lots(flows, rates, cdi_percent, start, end, True)[1]