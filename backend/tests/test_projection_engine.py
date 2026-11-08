from decimal import Decimal, ROUND_HALF_UP

from app.services.projection_engine import run_projection

RATE = Decimal("0.01")  # 1% ao mês, só para facilitar as contas


def project(**overrides):
    params = {
        "initial_amount": Decimal("0"),
        "monthly_deposit": Decimal("0"),
        "monthly_withdrawal": Decimal("0"),
        "withdrawal_start_month": 1,
        "horizon_months": 3,
        "monthly_rate": RATE,
    }
    return run_projection(**{**params, **overrides})


def test_initial_amount_grows_with_compound_interest():
    result = project(initial_amount=Decimal("1000"))

    last = result.points[-1]
    assert last.gross_balance == Decimal("1030.301")  # 1000 x 1,01^3
    assert last.invested == Decimal("1000")
    assert last.tax_estimated == Decimal("6.817725")  # 30,301 de rendimento x 22,5%
    assert last.net_balance == Decimal("1023.483275")


def test_monthly_deposits_start_earning_next_month():
    result = project(monthly_deposit=Decimal("100"))

    last = result.points[-1]
    assert last.gross_balance == Decimal("303.01")  # 100 + 101 + 102,01 de aportes rendidos
    assert last.invested == Decimal("300")


def test_partial_withdrawal_takes_proportional_principal():
    result = project(
        initial_amount=Decimal("1000"), monthly_withdrawal=Decimal("505"), horizon_months=1
    )

    last = result.points[-1]
    assert last.gross_balance == Decimal("505")  # 1010 - 505
    assert last.invested == Decimal("500")  # saiu metade do aportado e metade do rendimento
    assert last.tax_paid == Decimal("1.125")  # 5 de rendimento x 22,5%
    assert last.withdrawn == Decimal("505")


def test_withdrawals_wait_for_their_start_month():
    result = project(
        initial_amount=Decimal("1000"),
        monthly_withdrawal=Decimal("100"),
        withdrawal_start_month=3,
        horizon_months=2,
    )

    assert result.points[-1].withdrawn == 0
    assert result.points[-1].gross_balance == Decimal("1020.1")  # 1000 x 1,01^2


def test_money_running_out_is_reported_not_raised():
    result = project(initial_amount=Decimal("100"), monthly_withdrawal=Decimal("500"))

    assert result.depleted_month == 1
    assert result.points[-1].gross_balance == 0
    assert result.points[-1].withdrawn == Decimal("101")  # só havia 100 + 1 de rendimento


def test_tax_rate_drops_after_six_months():
    result = project(initial_amount=Decimal("1000"), horizon_months=7)

    last = result.points[-1]  # mês 7: 210 dias, faixa de 20%
    expected_yield = Decimal("1000") * Decimal("1.01") ** 7 - Decimal("1000")
    assert last.tax_estimated == expected_yield * Decimal("0.20")


def test_matured_projection_lot_pays_tax_and_restarts_at_month_24():
    result = project(initial_amount=Decimal("1000"), horizon_months=25)

    gross_at_maturity = Decimal("1000") * (1 + RATE) ** 24
    tax = ((gross_at_maturity - Decimal("1000")) * Decimal("0.15")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    reinvested = (gross_at_maturity - tax).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    maturity = result.points[23]
    next_month = result.points[24]
    assert maturity.gross_balance == reinvested
    assert maturity.invested == Decimal("1000")
    assert maturity.tax_paid == tax
    assert next_month.gross_balance == reinvested * (1 + RATE)
    assert next_month.invested == Decimal("1000")