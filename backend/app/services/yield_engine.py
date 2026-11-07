from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

MAX_GAP_DAYS = 5  # fim de semana somado a um feriado prolongado


class CdiCoverageError(Exception):
    """O CDI gravado não cobre o período que se quer calcular."""


@dataclass(frozen=True)
class Flow:
    """Uma movimentação: valor positivo é aporte, negativo é retirada."""

    day: date
    amount: Decimal


@dataclass(frozen=True)
class DayPoint:
    day: date
    balance: Decimal  # saldo no fim do dia
    yield_amount: Decimal  # quanto rendeu naquele dia


def daily_yield_rate(daily_rate: Decimal, cdi_percent: Decimal) -> Decimal:
    """CDI do dia (em % ao dia) vezes o percentual da caixinha, como fração.

    Exemplo: CDI de 0,05% ao dia e caixinha de 110% -> 0,00055.
    """
    return (daily_rate / 100) * (cdi_percent / 100)


def _check_coverage(rates: dict[date, Decimal], start: date, end: date) -> None:
    too_early = start < min(rates, default=start) - timedelta(days=MAX_GAP_DAYS)
    if not rates or end > max(rates) or too_early:
        raise CdiCoverageError("O CDI gravado não cobre o período pedido.")


def simulate(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
) -> list[DayPoint]:
    """Calcula o saldo e o rendimento de cada dia, de start até end.

    Em cada dia: primeiro rende (se for dia útil), depois entram as movimentações.
    """
    if start > end:
        return []
    _check_coverage(rates, start, end)

    flows_by_day: dict[date, Decimal] = defaultdict(Decimal)
    for flow in flows:
        flows_by_day[flow.day] += flow.amount

    balance = Decimal("0")
    points: list[DayPoint] = []
    day = start
    while day <= end:
        earned = Decimal("0")
        if day in rates:  # só dias úteis têm CDI
            earned = balance * daily_yield_rate(rates[day], cdi_percent)
            balance += earned
        balance += flows_by_day.get(day, Decimal("0"))
        points.append(DayPoint(day=day, balance=balance, yield_amount=earned))
        day += timedelta(days=1)
    return points


def monthly_yields(points: list[DayPoint]) -> list[tuple[str, Decimal]]:
    """Soma o rendimento de cada mês, no formato [("2025-01", valor), ...]."""
    totals: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
    for point in points:
        totals[(point.day.year, point.day.month)] += point.yield_amount
    return [(f"{year}-{month:02d}", total) for (year, month), total in sorted(totals.items())]


def to_cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)