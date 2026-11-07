from datetime import date
from decimal import Decimal

import pytest

from app.services.tax_engine import InsufficientBalanceError, ir_rate, simulate_lots
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
    assert ir_rate(720) == Decimal("0.175")
    assert ir_rate(721) == Decimal("0.15")


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