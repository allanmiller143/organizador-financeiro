from datetime import date
from decimal import Decimal

import pytest

from app.services.yield_engine import (
    CdiCoverageError,
    Flow,
    daily_yield_rate,
    monthly_yields,
    simulate,
    to_cents,
)

# CDI fictício de 1% ao dia, só em dias úteis (11 e 12 de janeiro são fim de semana).
RATES = {date(2025, 1, d): Decimal("1") for d in (6, 7, 8, 9, 10, 13)}
HUNDRED = Decimal("100")


def balance_on(points, day):
    return next(p.balance for p in points if p.day == day)


def test_daily_yield_rate_applies_cdi_percent():
    assert daily_yield_rate(Decimal("1"), Decimal("100")) == Decimal("0.01")
    assert daily_yield_rate(Decimal("1"), Decimal("110")) == Decimal("0.011")


def test_deposit_starts_earning_next_business_day():
    flows = [Flow(date(2025, 1, 6), Decimal("1000"))]

    points = simulate(flows, RATES, HUNDRED, date(2025, 1, 6), date(2025, 1, 8))

    assert points[0].yield_amount == 0  # no dia do aporte ainda não rende
    assert balance_on(points, date(2025, 1, 6)) == Decimal("1000")
    assert balance_on(points, date(2025, 1, 7)) == Decimal("1010")
    assert balance_on(points, date(2025, 1, 8)) == Decimal("1020.10")  # juro composto


def test_weekend_does_not_earn():
    flows = [Flow(date(2025, 1, 10), Decimal("1000"))]

    points = simulate(flows, RATES, HUNDRED, date(2025, 1, 10), date(2025, 1, 13))

    assert balance_on(points, date(2025, 1, 11)) == Decimal("1000")
    assert balance_on(points, date(2025, 1, 12)) == Decimal("1000")
    assert balance_on(points, date(2025, 1, 13)) == Decimal("1010")


def test_withdrawal_comes_after_the_days_yield():
    flows = [
        Flow(date(2025, 1, 6), Decimal("1000")),
        Flow(date(2025, 1, 8), Decimal("-500")),
    ]

    points = simulate(flows, RATES, HUNDRED, date(2025, 1, 6), date(2025, 1, 8))

    last = points[-1]
    assert last.yield_amount == Decimal("10.10")  # rendeu sobre 1010 antes de sacar
    assert last.balance == Decimal("520.10")  # 1020,10 - 500


def test_110_percent_of_cdi_earns_more():
    flows = [Flow(date(2025, 1, 6), Decimal("1000"))]

    points = simulate(flows, RATES, Decimal("110"), date(2025, 1, 6), date(2025, 1, 7))

    assert balance_on(points, date(2025, 1, 7)) == Decimal("1011")


def test_monthly_yields_split_by_month():
    rates = {date(2025, 1, 30): Decimal("1"), date(2025, 1, 31): Decimal("1"), date(2025, 2, 3): Decimal("1")}
    flows = [Flow(date(2025, 1, 29), Decimal("1000"))]

    points = simulate(flows, rates, HUNDRED, date(2025, 1, 29), date(2025, 2, 3))

    assert monthly_yields(points) == [
        ("2025-01", Decimal("20.10")),  # 10,00 + 10,10
        ("2025-02", Decimal("10.201")),
    ]


def test_missing_cdi_coverage_raises():
    flows = [Flow(date(2025, 1, 6), Decimal("1000"))]

    with pytest.raises(CdiCoverageError):
        simulate(flows, RATES, HUNDRED, date(2025, 1, 6), date(2025, 1, 31))


def test_to_cents_rounds_half_up():
    assert to_cents(Decimal("1020.105")) == Decimal("1020.11")
    assert to_cents(Decimal("1020.104")) == Decimal("1020.10")