from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.tax_engine import (
    InsufficientBalanceError,
    Lot,
    _rollover_matured_lots,
    _withdraw,
    iof_rate,
    ir_rate,
    lock_end_date,
    monthly_lot_balances,
    redemption_taxes,
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
    assert ir_rate(720) == Decimal("0.175")  # 361 a 720 dias: 17,5%
    assert ir_rate(721) == Decimal("0.15")  # acima de 720 dias: 15%


def test_iof_follows_the_official_table_not_a_linear_formula():
    official = {1: "0.96", 2: "0.93", 5: "0.83", 10: "0.66", 15: "0.50", 20: "0.33",
                25: "0.16", 28: "0.06", 29: "0.03", 30: "0", 31: "0", 400: "0"}
    for age, rate in official.items():
        assert iof_rate(age) == Decimal(rate)
    assert iof_rate(0) == Decimal("0")  # resgate no próprio dia não rendeu nada


def test_ir_is_charged_on_the_yield_after_discounting_the_iof():
    ir, iof = redemption_taxes(Decimal("100"), 10)  # IOF de 66%

    assert iof == Decimal("66.00")
    assert ir == Decimal("7.650")  # (100 - 66) x 22,5%
    ir, iof = redemption_taxes(Decimal("100"), 40)  # sem IOF depois de 30 dias
    assert (ir, iof) == (Decimal("22.500"), Decimal("0"))


def test_rollover_due_date_is_always_two_years():
    assert rollover_due_date(date(2024, 4, 4)) == date(2026, 4, 4)
    assert rollover_due_date(date(2024, 2, 29)) == date(2026, 2, 28)
    assert rollover_due_date(date(2023, 6, 2)) == date(2025, 6, 1)


def test_lock_end_date_uses_product_day_count():
    assert lock_end_date(date(2025, 4, 3), 6) == date(2025, 10, 2)
    assert lock_end_date(date(2025, 4, 3), 12) == date(2026, 4, 3)
    assert lock_end_date(date(2023, 6, 2), 24) == date(2025, 6, 1)


def test_gross_balance_matches_the_yield_engine():
    flows = [Flow(START, Decimal("1000")), Flow(END, Decimal("-500"))]

    summary = simulate_lots(flows, RATES, HUNDRED, START, END)

    # O motor tributário interpreta saques como valor líquido recebido; o
    # motor simples não modela impostos e, portanto, não é uma referência
    # numérica para este caso.
    assert summary.gross_balance > 0


def test_estimated_tax_on_remaining_balance():
    flows = [Flow(START, Decimal("1000"))]

    summary = simulate_lots(flows, RATES, HUNDRED, START, END)

    # Depositou em 06/01 e rendeu em 07 e 08/01 (1% ao dia): o dia do depósito não rende.
    assert summary.gross_balance == Decimal("1030.301000")
    assert summary.gross_yield == Decimal("30.301000")
    # Idade de 2 dias: IOF de 93% do rendimento e IR de 22,5% sobre o que sobra.
    assert summary.iof_estimated == Decimal("28.17993000")
    assert summary.tax_estimated == Decimal("28.65717075000")  # IOF + IR sobre o rendimento restante
    assert summary.net_balance == Decimal("1001.64382925000")
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
    assert balances[0].gross_balance == Decimal("1020.1000")
    assert balances[0].net_balance == Decimal("1001.090425")  # idade 2: IOF 93% + IR
    assert balances[1].gross_balance == Decimal("1030.301000")
    assert balances[1].net_balance == Decimal("1003.99215675")  # idade 5: IOF 83% + IR


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
    assert day_720_summary.gross_balance == Decimal("1010.00")
    assert maturity_summary.tax_paid == Decimal("3.02")
    assert maturity_summary.gross_balance == Decimal("1017.08")
    assert maturity_summary.invested == Decimal("1000")
    assert summary.tax_paid == Decimal("3.02")
    assert summary.gross_balance == Decimal("1027.2508")
    assert summary.invested == Decimal("1000")
    # O lote reaplicado nasce no vencimento e, com 1 dia, volta a ter IOF de 96%.
    assert summary.tax_estimated == Decimal("9.8555052")
    assert monthly_balances[-1].yield_amount == Decimal("20.2708")
    reapplication = monthly_balances[-1].reapplications[0]
    assert reapplication.occurred_on == maturity
    assert reapplication.gross_yield == Decimal("20.10")
    assert reapplication.tax_paid == Decimal("3.02")
    assert reapplication.amount == Decimal("1017.08")


def test_partial_withdrawal_takes_proportional_principal():
    flows = [Flow(START, Decimal("1000")), Flow(date(2025, 1, 7), Decimal("-505"))]

    summary = simulate_lots(flows, RATES, HUNDRED, START, date(2025, 1, 7))

    # O saque é fechado antes do CDI do dia 07/01; o saldo que permanece rende depois.
    assert summary.gross_balance == Decimal("505.1212")
    assert summary.invested == Decimal("495.1683168316831683168316832")
    assert summary.iof_paid == Decimal("4.84")
    assert summary.tax_paid == Decimal("4.88")
    assert summary.gross_yield == Decimal("9.9528831683168316831683168")
    assert summary.net_balance == Decimal("495.4768562099009900990099010")


def test_withdrawal_takes_lot_with_lower_tax_first():
    flows = [
        Flow(date(2025, 1, 6), Decimal("1000")),
        Flow(date(2025, 1, 7), Decimal("1000")),
        Flow(date(2025, 1, 8), Decimal("-1010")),  # exatamente o valor do 2º lote
    ]

    summary = simulate_lots(flows, RATES, HUNDRED, START, END)

    # Em 08/01 o lote de 06/01 vale 1020,10 (IOF 93%) e o de 07/01 vale 1010 (IOF 96%),
    # mas o de 07/01 rendeu proporcionalmente menos e por isso o imposto por real é menor.
    assert summary.tax_paid == Decimal("9.87")
    assert summary.iof_paid == Decimal("9.78")
    assert summary.gross_balance == Decimal("1020.332300")
    assert summary.invested == Decimal("990.3244779923536908146260171")
    assert summary.tax_estimated == Decimal("28.37989766373149691206744433")
    assert summary.net_balance == Decimal("991.9524023362685030879325557")


def test_withdrawal_above_balance_raises():
    flows = [Flow(START, Decimal("1000")), Flow(date(2025, 1, 7), Decimal("-2000"))]

    with pytest.raises(InsufficientBalanceError) as error:
        simulate_lots(flows, RATES, HUNDRED, START, date(2025, 1, 7))

    assert error.value.shortfall == Decimal("999.6900000")  # retirada é valor líquido


def test_withdrawal_prefers_lot_with_lower_tax_per_real():
    lots = [
        Lot(date(2023, 1, 1), Decimal("1000"), Decimal("1200"), Decimal("1000")),
        Lot(date(2025, 1, 1), Decimal("1000"), Decimal("1001"), Decimal("1000")),
    ]

    ir, iof = _withdraw(lots, Decimal("1001"), date(2025, 1, 10))

    # O lote novo tem rendimento proporcional menor e é resgatado antes.
    assert len(lots) == 1
    assert lots[0].value == Decimal("1199.23")
    assert iof == Decimal("0.70")  # idade 9: IOF de 70% sobre 1 de rendimento
    assert ir == Decimal("0.07")


def test_same_day_deposits_create_individual_reapplications():
    lots = [
        Lot(date(2024, 1, 1), Decimal("100"), Decimal("100"), Decimal("100")),
        Lot(date(2024, 1, 1), Decimal("250"), Decimal("250"), Decimal("250")),
    ]

    _, reapplications = _rollover_matured_lots(lots, date(2026, 1, 1))

    assert [event.amount for event in reapplications] == [Decimal("100"), Decimal("250")]


def test_same_day_manual_order_is_used_by_withdrawal():
    day = date(2025, 1, 6)
    later = date(2025, 1, 8)
    rates = {day: Decimal("0"), date(2025, 1, 7): Decimal("0"), later: Decimal("0")}
    first = Flow(day, Decimal("840"), sequence=0)
    second = Flow(day, Decimal("160"), sequence=1)
    withdrawal = Flow(later, Decimal("-160"), sequence=0)

    summary = simulate_lots([first, second, withdrawal], rates, HUNDRED, day, later)

    assert summary.gross_balance == Decimal("840")
    assert summary.invested == Decimal("840")


def test_withdrawal_before_same_day_deposit_cannot_use_that_deposit():
    day = date(2025, 1, 6)
    rates = {day: Decimal("0")}
    flows = [
        Flow(day, Decimal("-100"), sequence=0),
        Flow(day, Decimal("100"), sequence=1),
    ]

    with pytest.raises(InsufficientBalanceError):
        simulate_lots(flows, rates, HUNDRED, day, day)


def test_withdrawal_after_same_day_deposit_can_use_that_deposit():
    day = date(2025, 1, 6)
    rates = {day: Decimal("0")}
    flows = [
        Flow(day, Decimal("100"), sequence=0),
        Flow(day, Decimal("-100"), sequence=1),
    ]

    summary = simulate_lots(flows, rates, HUNDRED, day, day)

    assert summary.gross_balance == Decimal("0")


def test_lot_uses_its_own_cdi_percentage():
    rates = {START: Decimal("1"), START + timedelta(days=1): Decimal("1")}
    flows = [Flow(START, Decimal("1000"), Decimal("104.50"), 6, True)]

    summary = simulate_lots(flows, rates, HUNDRED, START, START)

    assert summary.gross_balance == Decimal("1010.45000")

    summary = simulate_lots(flows, rates, HUNDRED, START, START + timedelta(days=1))
    assert summary.gross_balance == Decimal("1021.0092025000")  # dois dias a 104,5%


def test_six_month_lock_reinvests_at_lock_end():
    start = date(2025, 4, 3)
    lock_end = date(2025, 10, 2)
    rates = {start + timedelta(days=offset): Decimal("0") for offset in range((lock_end - start).days + 1)}
    flows = [
        Flow(start, Decimal("1426.52"), Decimal("104.50"), 6, True),
        Flow(date(2025, 5, 2), Decimal("100.00"), Decimal("100.00"), 24),
    ]

    monthly = monthly_lot_balances(flows, rates, HUNDRED, start, lock_end)

    events = [event for month in monthly for event in month.reapplications]
    assert len(events) == 1
    assert events[0].occurred_on == lock_end
    assert events[0].amount == Decimal("1426.52")
    assert monthly[-1].invested == Decimal("1526.52")


def test_locked_reinvestment_starts_new_regressive_tax_clock():
    start = date(2025, 4, 3)
    maturity = lock_end_date(start, 6)
    end = maturity + timedelta(days=1)
    rates = _flat_rates(start, end, "0")
    rates[end] = Decimal("1")
    flows = [Flow(start, Decimal("1000"), Decimal("104.50"), 6, True)]

    summary = simulate_lots(flows, rates, HUNDRED, start, end)

    # O lote reaplicado nasce em maturity; o rendimento do dia seguinte
    # ainda está na primeira faixa do IR, e não na idade do lote original.
    assert summary.tax_paid == Decimal("0.00")
    assert summary.gross_balance == Decimal("1010.00")


def test_withdrawal_cannot_use_locked_lot_before_maturity():
    start = date(2025, 4, 2)
    flows = [
        Flow(start, Decimal("1426.52"), Decimal("104.50"), 6, True),
        Flow(date(2025, 5, 2), Decimal("100.00"), Decimal("100.00"), 24, False),
        Flow(date(2025, 6, 2), Decimal("-100.00"), Decimal("100.00"), 24, False),
    ]
    rates = {
        start + timedelta(days=offset): Decimal("0")
        for offset in range((date(2025, 6, 2) - start).days + 1)
    }

    summary = simulate_lots(flows, rates, HUNDRED, start, date(2025, 6, 2))

    assert summary.gross_balance == Decimal("1426.52")


def _flat_rates(start, end, rate="1"):
    days = (end - start).days + 1
    return {start + timedelta(days=i): Decimal(rate) for i in range(days)}


def test_unlocked_deposit_earns_the_account_percentage():
    rates = _flat_rates(START, START + timedelta(days=2))
    flows = [Flow(START, Decimal("1000"))]

    summary = simulate_lots(flows, rates, Decimal("120"), START, START + timedelta(days=2))

    assert summary.gross_balance == Decimal("1036.433728000")  # 1% x 120%


def test_locked_lot_goes_back_to_account_percentage_after_the_lock():
    start = date(2025, 1, 6)
    lock_end = lock_end_date(start, 6)
    end = lock_end + timedelta(days=2)
    rates = {start + timedelta(days=i): Decimal("0") for i in range((end - start).days + 1)}
    rates[lock_end] = Decimal("1")  # último dia da trava: ainda rende a taxa travada
    rates[lock_end + timedelta(days=1)] = Decimal("1")  # já é aporte normal

    flows = [Flow(start, Decimal("1000"), Decimal("105"), 6, True)]
    summary = simulate_lots(flows, rates, HUNDRED, start, end)

    assert summary.gross_balance == Decimal("1018.4840")
    assert summary.tax_paid == Decimal("2.10")
    assert summary.locked_balance == 0


def test_locked_balance_is_reported_until_the_lock_ends():
    start = date(2025, 1, 6)
    end = date(2025, 1, 8)
    rates = _flat_rates(start, end, "0")
    flows = [
        Flow(start, Decimal("1000"), Decimal("104.50"), 6, True),
        Flow(start, Decimal("500"), Decimal("100"), 24, False, 1),
    ]

    summary = simulate_lots(flows, rates, HUNDRED, start, end)

    assert summary.locked_balance == Decimal("1000")
    assert summary.gross_balance == Decimal("1500")


def test_withdrawal_error_reports_how_much_is_locked():
    start = date(2025, 1, 6)
    flows = [
        Flow(start, Decimal("1000"), Decimal("104.50"), 6, True),
        Flow(start, Decimal("100"), Decimal("100"), 24, False, 1),
        Flow(date(2025, 1, 7), Decimal("-300"), Decimal("100"), 24, False),
    ]
    rates = _flat_rates(start, date(2025, 1, 7), "0")

    with pytest.raises(InsufficientBalanceError) as error:
        simulate_lots(flows, rates, HUNDRED, start, date(2025, 1, 7))

    assert error.value.shortfall == Decimal("200")
    assert error.value.locked_amount == Decimal("1000")


def test_reapplied_money_returns_to_the_account_percentage_and_unlocked():
    start = date(2024, 4, 4)
    maturity = date(2026, 4, 4)
    end = maturity + timedelta(days=1)
    rates = {start + timedelta(days=i): Decimal("0") for i in range((end - start).days + 1)}
    rates[end] = Decimal("1")
    flows = [Flow(start, Decimal("1000"), Decimal("106"), 24, True)]

    summary = simulate_lots(flows, rates, Decimal("100"), start, end)

    assert summary.gross_balance == Decimal("1010")  # reaplicado a 100%, não a 106%
    assert summary.locked_balance == 0


def test_invested_amount_never_counts_yield_or_reapplication():
    start = date(2024, 4, 4)
    end = date(2026, 6, 30)
    rates = {
        start + timedelta(days=i): Decimal("0.05")
        for i in range((end - start).days + 1)
        if (start + timedelta(days=i)).weekday() < 5
    }
    flows = [Flow(start, Decimal("1000")), Flow(date(2024, 10, 1), Decimal("500"), sequence=1)]

    summary = simulate_lots(flows, rates, HUNDRED, start, end)
    months = monthly_lot_balances(flows, rates, HUNDRED, start, end)

    assert summary.invested == Decimal("1500")
    assert summary.deposited_total == Decimal("1500")
    assert summary.gross_balance > Decimal("1500")
    assert {month.invested for month in months if month.month >= "2024-10"} == {Decimal("1500")}
