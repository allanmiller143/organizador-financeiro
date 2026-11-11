"""Caixinhas reais do Nubank (RDB, 120% do CDI) usadas para calibrar a simulação.

CDI de 2026 aproximado em 14,15% a.a. (base 252). Os valores em reais têm tolerância de
alguns centavos porque o CDI exato varia dia a dia. O motor recalcula o custo efetivo de
cada parcela em centavos; a correspondência exata com o extrato RDB é protegida em
`test_rdb_statement_reference.py`.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.services.calendar_br import (
    brazil_holidays,
    build_cdi_rates,
    daily_rate_from_annual,
    is_business_day,
    next_business_day,
)
from app.services.deposit_detail_service import (
    PRODUCT_IMMEDIATE,
    PRODUCT_PLANNED,
    calculate_deposit_details,
)
from app.services.tax_engine import IOF_PERCENT_BY_DAY, iof_rate, ir_rate, simulate_lots
from app.services.yield_engine import Flow

D = Decimal
BASE = D("120.00")
START = date(2026, 6, 1)
END = date(2026, 11, 9)
RATES = build_cdi_rates(START, END, D("14.15"))
CENTS = D("0.05")  # tolerância "de alguns centavos"


def close(value, expected, tolerance=CENTS):
    return abs(D(value) - D(expected)) <= tolerance


def run(deposits, withdrawals, end):
    """deposits/withdrawals: listas de (data, valor). Retorna {(data, valor): item} e a lista."""
    flows = [Flow(day, D(amount), sequence=i) for i, (day, amount) in enumerate(deposits)]
    flows += [Flow(day, -D(amount), sequence=100 + i) for i, (day, amount) in enumerate(withdrawals)]
    return calculate_deposit_details(flows, RATES, BASE, START, end)


def by_date(details, day):
    return [item for item in details if item["deposited_on"] == day]


# --------------------------------------------------------------------------- calendário


def test_brazilian_national_holidays_of_2026():
    holidays = brazil_holidays(2026)

    assert date(2026, 2, 16) in holidays and date(2026, 2, 17) in holidays  # Carnaval
    assert date(2026, 4, 3) in holidays  # Sexta-feira Santa
    assert date(2026, 6, 4) in holidays  # Corpus Christi
    assert date(2026, 9, 7) in holidays
    assert date(2026, 10, 12) in holidays
    assert date(2026, 11, 2) in holidays
    assert date(2026, 11, 20) in holidays  # Consciência Negra
    assert date(2026, 6, 5) not in holidays


def test_business_days_skip_weekends_and_holidays():
    assert not is_business_day(date(2026, 6, 4))  # feriado
    assert not is_business_day(date(2026, 6, 6))  # sábado
    assert is_business_day(date(2026, 6, 5))
    assert next_business_day(date(2026, 6, 3)) == date(2026, 6, 5)  # pula Corpus Christi
    assert next_business_day(date(2026, 9, 4)) == date(2026, 9, 8)  # fim de semana + 07/09


def test_cdi_rates_are_configurable_per_date_and_only_on_business_days():
    assert date(2026, 6, 4) not in RATES and date(2026, 6, 6) not in RATES
    assert date(2026, 6, 5) in RATES
    daily = daily_rate_from_annual(D("14.15"))
    assert close(daily, "0.05253", D("0.00001"))  # % ao dia
    assert (1 + daily / 100) ** 252 - 1 - D("0.1415") < D("1e-12")


# --------------------------------------------------------------------------- IR e IOF


def test_official_iof_table_has_no_linear_shortcut():
    expected = [96, 93, 90, 86, 83, 80, 76, 73, 70, 66, 63, 60, 56, 53, 50,
                46, 43, 40, 36, 33, 30, 26, 23, 20, 16, 13, 10, 6, 3, 0]
    assert [int(IOF_PERCENT_BY_DAY[day] * 100) for day in range(1, 31)] == expected
    assert iof_rate(31) == 0 and iof_rate(500) == 0
    assert iof_rate(10) == D("0.66")
    assert iof_rate(10) != D(30 - 10) / 30  # a fórmula linear (66,67%) não vale
    assert iof_rate(1) != D(30 - 1) / 30  # linear daria 96,67%; a tabela oficial é 96%


def test_ir_brackets_by_calendar_days():
    assert ir_rate(180) == D("0.225") and ir_rate(181) == D("0.20")
    assert ir_rate(360) == D("0.20") and ir_rate(361) == D("0.175")
    assert ir_rate(720) == D("0.175") and ir_rate(721) == D("0.15")


# --------------------------------------------------------------------------- rendimento


def test_deposit_earns_on_the_same_business_day():
    friday = date(2026, 6, 5)
    monday = date(2026, 6, 8)
    flows = [Flow(friday, D("1000"))]

    through_weekend = simulate_lots(flows, RATES, BASE, START, date(2026, 6, 7))
    first_day = simulate_lots(flows, RATES, BASE, START, monday)

    daily_growth = daily_rate_from_annual(D("14.15")) * D("1.2") / 100
    assert through_weekend.gross_balance == D("1000") * (1 + daily_growth)
    assert first_day.gross_balance == through_weekend.gross_balance * (1 + daily_growth)


def test_no_yield_on_the_corpus_christi_holiday():
    flows = [Flow(date(2026, 6, 3), D("1000"))]

    before = simulate_lots(flows, RATES, BASE, START, date(2026, 6, 3))
    holiday = simulate_lots(flows, RATES, BASE, START, date(2026, 6, 4))

    assert before.gross_balance == holiday.gross_balance and before.gross_balance > D("1000")


# --------------------------------------------------------------------------- Caixinha 1


CAIXINHA_1_DEPOSITS = [
    (date(2026, 6, 3), "1125"),
    (date(2026, 6, 11), "2750"),
    (date(2026, 6, 12), "825"),
]
CAIXINHA_1_WITHDRAWALS = [
    (date(2026, 6, 16), "500"),
    (date(2026, 6, 28), "16"),
    (date(2026, 6, 29), "200"),
]


def test_caixinha_1_each_withdrawal_comes_from_the_expected_lot():
    details = run(CAIXINHA_1_DEPOSITS, CAIXINHA_1_WITHDRAWALS, date(2026, 6, 30))

    lot_03, lot_11, lot_12 = (by_date(details, date(2026, 6, day))[0] for day in (3, 11, 12))
    assert lot_03["partial_withdrawals"] == D("216.00")
    assert lot_12["partial_withdrawals"] == D("500.00")
    assert lot_11["partial_withdrawals"] == D("0.00")
    assert [w["amount"] for w in lot_12["withdrawals"]] == [D("500.00")]
    assert [(w["occurred_on"], w["amount"]) for w in lot_03["withdrawals"]] == [
        (date(2026, 6, 28), D("16.00")),
        (date(2026, 6, 29), D("200.00")),
    ]


def test_caixinha_1_iof_and_ir_are_reported_per_withdrawal():
    details = run(CAIXINHA_1_DEPOSITS, CAIXINHA_1_WITHDRAWALS, date(2026, 6, 30))
    lot_12 = by_date(details, date(2026, 6, 12))[0]
    lot_03 = by_date(details, date(2026, 6, 3))[0]

    withdrawal = lot_12["withdrawals"][0]  # 4 dias de idade: IOF de 86%
    assert withdrawal["iof"] > 0 and withdrawal["income_tax"] >= 0
    # IR = (rendimento - IOF) x 22,5%
    expected_ir = (withdrawal["gross_yield"] - withdrawal["iof"]) * D("0.225")
    assert close(withdrawal["income_tax"], expected_ir, D("0.02"))
    assert close(lot_12["iof"], "0.55", D("0.05"))
    assert close(lot_03["iof"], "0.31", D("0.05"))  # Nubank: 0,31 (idades de 25 e 26 dias)


def test_caixinha_1_partial_lot_keeps_principal_and_yield_proportionally():
    details = run(CAIXINHA_1_DEPOSITS, CAIXINHA_1_WITHDRAWALS, date(2026, 6, 30))
    lot_03 = by_date(details, date(2026, 6, 3))[0]

    assert lot_03["applied_amount"] == D("1125.00")  # principal original não muda
    assert lot_03["principal_remaining"] < D("1225.00")
    assert lot_03["gross_balance"] > lot_03["principal_remaining"]  # rendimento não foi zerado
    # o que saiu era proporcional: principal restante / valor atual não mudou
    share_left = lot_03["principal_remaining"] / lot_03["gross_balance"]
    assert D("0.98") < share_left < D("1")


# --------------------------------------------------------------------------- Caixinha 2


def _caixinha_2():
    d = date
    deposits = [
        (d(2026, 9, 4), "1000"),
        (d(2026, 9, 18), "1500"),
        (d(2026, 9, 29), "500"),
        (d(2026, 9, 29), "621"),
        (d(2026, 9, 29), "30"),
        (d(2026, 9, 29), "300"),
        (d(2026, 9, 29), "5"),
        (d(2026, 10, 3), "1500"),
        (d(2026, 10, 14), "3000"),
        (d(2026, 11, 4), "2300"),
    ]
    withdrawals = [
        (d(2026, 9, 9), "290"),
        (d(2026, 9, 11), "666"),
        (d(2026, 9, 20), "1500"),
        (d(2026, 10, 18), "1000"),
        (d(2026, 10, 28), "422"),
        (d(2026, 11, 4), "1500"),
    ]
    return run(deposits, withdrawals, END)


def test_caixinha_2_lot_of_september_4th_with_accumulated_iof():
    lot = by_date(_caixinha_2(), date(2026, 9, 4))[0]

    assert lot["partial_withdrawals"] == D("956.00")  # 290 + 666
    assert [w["amount"] for w in lot["withdrawals"]] == [D("290.00"), D("666.00")]
    assert close(lot["iof"], "1.58", D("0.08"))


def test_caixinha_2_lot_of_september_18th_is_fully_withdrawn_and_disappears():
    # O valor da retirada é líquido; o lote é encerrado quando o saldo líquido
    # exibido coincide com o valor sacado, sem deixar resíduo artificial.
    assert by_date(_caixinha_2(), date(2026, 9, 18)) == []


def test_caixinha_2_withdrawal_of_422_consumes_small_lots_then_uses_621_partially():
    details = _caixinha_2()
    lots_0929 = by_date(details, date(2026, 9, 29))
    by_applied = {lot["applied_amount"]: lot for lot in lots_0929}

    # Os lotes pequenos de R$ 5 e R$ 30 são totalmente encerrados e, portanto,
    # deixam de aparecer na lista de saldos ativos. O lote de R$ 621 fica parcial.
    assert D("5.00") not in by_applied and D("30.00") not in by_applied
    assert by_applied[D("621.00")]["partial_withdrawals"] == D("386.66")
    assert by_applied[D("300.00")]["partial_withdrawals"] == D("0.00")
    assert by_applied[D("500.00")]["partial_withdrawals"] == D("0.00")
    # Os lotes de 03/10 e de 14/10 (IOF bem mais alto) não participam desse resgate.
    assert by_date(details, date(2026, 10, 3))[0]["partial_withdrawals"] == D("0.00")


def test_caixinha_2_withdrawal_of_1000_comes_from_the_lot_of_october_14th():
    lot = by_date(_caixinha_2(), date(2026, 10, 14))[0]

    # O lote de 18/09 deixa um pequeno resíduo tributário que também entra no
    # resgate; o lote de 14/10, portanto, fornece R$ 999,93 líquidos no CDI aproximado.
    assert lot["partial_withdrawals"] == D("999.93")
    assert [w["occurred_on"] for w in lot["withdrawals"]] == [date(2026, 10, 18)]


def test_caixinha_2_same_day_deposit_and_withdrawal_use_the_new_lot():
    lot = by_date(_caixinha_2(), date(2026, 11, 4))[0]

    assert lot["applied_amount"] == D("2300.00")
    assert lot["partial_withdrawals"] == D("1500.00")
    assert lot["withdrawals"][0]["iof"] == D("0.00")  # lote do dia ainda não rendeu
    assert lot["principal_remaining"] == D("800.00")


# --------------------------------------------------------------------------- vencimentos


def test_planned_rdb_reapplies_as_immediate_rdb_at_the_base_rate():
    start = date(2025, 1, 6)
    flows = [Flow(start, D("1000"), D("105"), 6, True, 0)]  # RDB Planejado de 6 meses a 105%
    lock_end = start + timedelta(days=182)
    rates = build_cdi_rates(start, lock_end + timedelta(days=10), D("10"))

    before = calculate_deposit_details(flows, rates, D("100"), start, lock_end - timedelta(days=1))
    after = calculate_deposit_details(flows, rates, D("100"), start, lock_end + timedelta(days=3))

    assert before[0]["product"] == PRODUCT_PLANNED
    assert before[0]["locked"] is True and before[0]["cdi_percent"] == D("105")
    assert before[0]["maturity_on"] == lock_end
    assert len(after) == 1  # o lote travado foi substituído, não duplicado
    assert after[0]["product"] == PRODUCT_IMMEDIATE
    assert after[0]["deposited_on"] == lock_end  # novo lote, na data do vencimento
    assert after[0]["locked"] is False
    assert after[0]["cdi_percent"] == D("100")  # volta à taxa-base da caixinha, não os 105%


def test_planned_rdb_does_not_keep_the_contracted_rate_after_maturity():
    start = date(2025, 1, 6)
    lock_end = start + timedelta(days=182)
    end = lock_end + timedelta(days=1)
    # CDI zero até o vencimento isola o efeito: só o dia seguinte rende (1%).
    rates = {start + timedelta(days=i): D("0") for i in range((end - start).days + 1)}
    rates[end] = D("1")
    flows = [Flow(start, D("1000"), D("105"), 6, True, 0)]

    summary = simulate_lots(flows, rates, D("100"), start, end)

    assert summary.gross_balance == D("1010")  # 100% do CDI; a 105% seriam 1010,50
    assert summary.locked_balance == 0


def test_immediate_rdb_reapplies_in_the_same_product():
    start = date(2024, 1, 2)
    maturity = date(2026, 1, 1)
    rates = {start + timedelta(days=i): D("0") for i in range((maturity - start).days + 1)}
    flows = [Flow(start, D("1000"), sequence=0)]

    details = calculate_deposit_details(flows, rates, BASE, start, maturity)

    assert len(details) == 1
    assert details[0]["product"] == PRODUCT_IMMEDIATE
    assert details[0]["deposited_on"] == maturity
