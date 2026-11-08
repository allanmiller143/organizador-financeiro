from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.tax_engine import (
    InsufficientBalanceError,
    ir_rate,
    monthly_lot_balances,
    rollover_due_date,
    simulate_lots,
)
from app.services.yield_engine import Flow, simulate

RATES = {date(2025, 1, d): Decimal("1") for d in (6, 7, 8, 9, 10, 13)}
HUNDRED = Decimal("100")
START = date(2025, 1, 6)
END = date(2025, 1, 8)


def test_ir_rate_follows_regressive_table():
    assert ir_rate(0) == Decimal("0.225")
    assert ir_rate(180) == Decimal("0.225")
    assert ir_rate(181) == Decimal("0.20")
    assert ir_rate(360) == Decimal("0.20")
    assert ir_rate(361) == Decimal("0.175")
    assert ir_rate(719) == Decimal("0.175")
    assert ir_rate(720) == Decimal("0.15")
    assert ir_rate(721) == Decimal("0.15")


def test_rollover_due_date_uses_calendar_anniversary():
    assert rollover_due_date(date(2024, 4, 4)) == date(2026, 4, 4)
    assert rollover_due_date(date(2024, 2, 29)) == date(2026, 2, 28)


def test_gross_balance_matches_the_yield_engine():
    flows = [Flow(START, Decimal("1000")), Flow(END, Decimal("-500"))]

    summary = simulate_lots(flows, RATES, HUNDRED, START, END)

    assert summary.gross_balance == simulate(flows, RATES, HUNDRED, START, END)[-1].balance


def test_estimated_tax_on_remaining_balance():
    flows = [Flow(START, Decimal("1000"))]

    summary = simulate_lots(flows, RATES, HUNDRED, START, END)

    assert summary.gross_balance == Decimal("1020.10")
    assert summary.gross_yield == Decimal("20.10")
    assert summary.tax_estimated == Decimal("4.5225")  # 20,10 x 22,5%
    assert summary.net_balance == Decimal("1015.5775")
    assert summary.tax_paid == 0


def test_monthly_lot_balances_capture_each_month_end():
    rates = {
        date(2025, 1, 30): Decimal("1"),
        date(2025, 1, 31): Decimal("1"),
        date(2025, 2, 3): Decimal("1"),
    }
    flows = [Flow(date(2025, 1, 29), Decimal("1000"))]

    balances = monthly_lot_balances(
        flows, rates, HUNDRED, date(2025, 1, 29), date(2025, 2, 3)
    )

    assert [balance.month for balance in balances] == ["2025-01", "2025-02"]
    assert balances[0].gross_balance == Decimal("1020.10")
    assert balances[0].net_balance == Decimal("1015.5775")
    assert balances[1].gross_balance == Decimal("1030.3010")
    assert balances[1].net_balance == Decimal("1023.4832750")


def test_lot_rolls_over_on_two_year_anniversary_not_day_720():
    start = date(2024, 4, 4)
    day_720 = start + timedelta(days=720)
    maturity = date(2026, 4, 4)
    end = maturity + timedelta(days=1)
    rates = {
        start + timedelta(days=offset): Decimal("0")
        for offset in range((end - start).days + 1)
    }
    rates[day_720] = Decimal("1")
    rates[maturity] = Decimal("1")
    rates[end] = Decimal("1")
    flows = [Flow(start, Decimal("1000"))]

    day_720_summary = simulate_lots(flows, rates, HUNDRED, start, day_720)
    maturity_summary = simulate_lots(flows, rates, HUNDRED, start, maturity)
    summary = simulate_lots(flows, rates, HUNDRED, start, end)
    monthly_balances = monthly_lot_balances(flows, rates, HUNDRED, start, end)

    assert day_720_summary.tax_paid == 0
    assert day_720_summary.gross_balance == Decimal("1010")
    assert maturity_summary.tax_paid == Decimal("3.02")
    assert maturity_summary.gross_balance == Decimal("1017.08")
    assert maturity_summary.invested == Decimal("1000")
    assert summary.tax_paid == Decimal("3.02")
    assert summary.gross_balance == Decimal("1027.2508")
    assert summary.invested == Decimal("1000")
    assert summary.tax_estimated == Decimal("2.28843")
    assert monthly_balances[-1].yield_amount == Decimal("20.2708")
    reapplication = monthly_balances[-1].reapplications[0]
    assert reapplication.occurred_on == maturity
    assert reapplication.gross_yield == Decimal("20.10")
    assert reapplication.tax_paid == Decimal("3.02")
    assert reapplication.amount == Decimal("1017.08")


def test_partial_withdrawal_takes_proportional_principal():
    flows = [Flow(START, Decimal("1000")), Flow(date(2025, 1, 7), Decimal("-505"))]

    summary = simulate_lots(flows, RATES, HUNDRED, START, date(2025, 1, 7))

    # lote valia 1010 (1000 aportados + 10 de rendimento); sacar 505 é metade dele
    assert summary.gross_balance == Decimal("505")
    assert summary.invested == Decimal("500")
    assert summary.tax_paid == Decimal("1.125")  # 5 de rendimento x 22,5%
    assert summary.net_balance == Decimal("503.875")


def test_withdrawal_takes_oldest_lot_first():
    flows = [
        Flow(date(2025, 1, 6), Decimal("1000")),
        Flow(date(2025, 1, 7), Decimal("1000")),
        Flow(date(2025, 1, 8), Decimal("-1020.10")),  # exatamente o valor do 1º lote
    ]

    summary = simulate_lots(flows, RATES, HUNDRED, START, END)

    assert summary.tax_paid == Decimal("4.5225")  # 20,10 de rendimento x 22,5%
    assert summary.gross_balance == Decimal("1010")  # sobrou só o 2º lote
    assert summary.invested == Decimal("1000")
    assert summary.tax_estimated == Decimal("2.25")  # 10 x 22,5%
    assert summary.net_balance == Decimal("1007.75")


def test_withdrawal_above_balance_raises():
    flows = [Flow(START, Decimal("1000")), Flow(date(2025, 1, 7), Decimal("-2000"))]

    with pytest.raises(InsufficientBalanceError) as error:
        simulate_lots(flows, RATES, HUNDRED, START, date(2025, 1, 7))

    assert error.value.shortfall == Decimal("990")  # saldo era 1010