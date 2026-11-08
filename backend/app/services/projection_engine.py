from dataclasses import dataclass
from decimal import Decimal

from app.services.tax_engine import (
    ROLLOVER_AGE_MONTHS,
    ir_rate,
    settle_matured_lot,
)

DAYS_PER_MONTH = 30  # aproximação: só para calcular a idade de cada aporte no imposto
CENT_TOLERANCE = Decimal("0.005")  # meio centavo


@dataclass
class _Lot:
    """Um aporte: em que dia (contado desde hoje) entrou, quanto foi e quanto vale agora."""

    start_day: int
    principal: Decimal
    value: Decimal
    invested: Decimal


@dataclass(frozen=True)
class MonthPoint:
    """O retrato do dinheiro no fim de um mês."""

    month: int
    gross_balance: Decimal
    invested: Decimal  # a parte do saldo que é dinheiro aportado
    tax_estimated: Decimal  # IR se resgatasse tudo neste mês
    net_balance: Decimal  # saldo bruto menos o IR estimado
    tax_paid: Decimal  # IR já retido nas retiradas (acumulado)
    withdrawn: Decimal  # total já retirado (acumulado, valor bruto)


@dataclass(frozen=True)
class ProjectionResult:
    points: list[MonthPoint]
    depleted_month: int | None  # primeiro mês em que o dinheiro acabou (None se não acabou)


def _withdraw(lots: list[_Lot], amount: Decimal, day: int) -> tuple[Decimal, Decimal]:
    """Retira dos lotes mais antigos primeiro.

    Devolve (quanto conseguiu retirar, imposto retido).
    Se o dinheiro não bastar, retira o que houver, e não dá erro.
    """
    remaining = amount
    tax = Decimal("0")
    for lot in lots:
        if remaining <= CENT_TOLERANCE:
            break
        take = min(remaining, lot.value)
        principal_out = lot.principal * (take / lot.value)  # tira aportado e rendimento na mesma proporção
        invested_out = lot.invested * (take / lot.value)
        tax += (take - principal_out) * ir_rate(day - lot.start_day)
        lot.principal -= principal_out
        lot.invested -= invested_out
        lot.value -= take
        remaining -= take
    lots[:] = [lot for lot in lots if lot.value > CENT_TOLERANCE]  # descarta lotes zerados
    return amount - remaining, tax


def run_projection(
    *,
    initial_amount: Decimal,
    monthly_deposit: Decimal,
    monthly_withdrawal: Decimal,
    withdrawal_start_month: int,
    horizon_months: int,
    monthly_rate: Decimal,
) -> ProjectionResult:
    """Anda mês a mês: rende, recebe o aporte e (se for a hora) faz a retirada."""
    lots: list[_Lot] = []
    if initial_amount > 0:
        lots.append(
            _Lot(
                start_day=0,
                principal=initial_amount,
                value=initial_amount,
                invested=initial_amount,
            )
        )

    tax_paid = Decimal("0")
    withdrawn = Decimal("0")
    depleted_month: int | None = None
    points: list[MonthPoint] = []

    for month in range(1, horizon_months + 1):
        day = month * DAYS_PER_MONTH

        # 1) o dinheiro que já está lá rende
        for lot in lots:
            lot.value *= 1 + monthly_rate

        # 2) entra o aporte do mês (começa a render no mês seguinte)
        if monthly_deposit > 0:
            lots.append(
                _Lot(
                    start_day=day,
                    principal=monthly_deposit,
                    value=monthly_deposit,
                    invested=monthly_deposit,
                )
            )

        # 3) sai a retirada do mês
        if monthly_withdrawal > 0 and month >= withdrawal_start_month:
            taken, tax = _withdraw(lots, monthly_withdrawal, day)
            withdrawn += taken
            tax_paid += tax
            if taken < monthly_withdrawal - CENT_TOLERANCE and depleted_month is None:
                depleted_month = month

        remaining_lots = []
        for lot in lots:
            if day - lot.start_day < ROLLOVER_AGE_MONTHS * DAYS_PER_MONTH:
                remaining_lots.append(lot)
                continue
            tax, reinvested = settle_matured_lot(lot.principal, lot.value)
            tax_paid += tax
            if reinvested > CENT_TOLERANCE:
                remaining_lots.append(
                    _Lot(
                        start_day=day,
                        principal=reinvested,
                        value=reinvested,
                        invested=lot.invested,
                    )
                )
        lots = remaining_lots

        # 4) tira o retrato do fim do mês
        gross = sum((lot.value for lot in lots), Decimal("0"))
        invested = sum((lot.invested for lot in lots), Decimal("0"))
        estimated = sum(
            ((lot.value - lot.principal) * ir_rate(day - lot.start_day) for lot in lots),
            Decimal("0"),
        )
        points.append(
            MonthPoint(
                month=month,
                gross_balance=gross,
                invested=invested,
                tax_estimated=estimated,
                net_balance=gross - estimated,
                tax_paid=tax_paid,
                withdrawn=withdrawn,
            )
        )

    return ProjectionResult(points=points, depleted_month=depleted_month)