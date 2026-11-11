"""Caixinha real do Nubank (120% do CDI) usada para calibrar as retiradas parciais.

Depósitos e retiradas vêm do app do Nubank. O CDI aqui é constante (aproximado), então os
valores em reais podem diferir em centavos; o que o teste trava é de QUAL depósito sai cada
retirada e como o rendimento bruto é contado.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.services.deposit_detail_service import calculate_deposit_details
from app.services.yield_engine import Flow

HOLIDAYS = {
    date(2026, 6, 4),
    date(2026, 9, 7),
    date(2026, 10, 12),
    date(2026, 11, 2),
}
BASE = Decimal("120.00")
START = date(2026, 6, 1)
END = date(2026, 11, 9)


def _rates():
    rates, day = {}, START
    while day <= END:
        if day.weekday() < 5 and day not in HOLIDAYS:
            rates[day] = Decimal("0.0517")  # % ao dia, aproximando o CDI de 2026
        day += timedelta(days=1)
    return rates


def _flows():
    deposits = [
        (date(2026, 6, 3), "1125.00"),
        (date(2026, 6, 11), "2750.00"),
        (date(2026, 6, 12), "825.00"),
        (date(2026, 7, 2), "1000.00"),
        (date(2026, 7, 10), "3000.00"),
        (date(2026, 8, 3), "510.00"),
        (date(2026, 8, 16), "1354.32"),
    ]
    withdrawals = [
        (date(2026, 6, 16), "500.00"),
        (date(2026, 6, 28), "16.00"),
        (date(2026, 6, 29), "200.00"),
    ]
    flows = [Flow(day, Decimal(amount), sequence=i) for i, (day, amount) in enumerate(deposits)]
    flows += [Flow(day, -Decimal(amount), sequence=10 + i) for i, (day, amount) in enumerate(withdrawals)]
    return flows


def _details():
    result = calculate_deposit_details(_flows(), _rates(), BASE, START, END)
    return {item["deposited_on"]: item for item in result}


def test_withdrawals_come_from_the_lot_with_lowest_ir_plus_iof():
    details = _details()

    # 16/06 (lotes com menos de 30 dias): sai do mais novo, que quase não rendeu.
    assert details[date(2026, 6, 12)]["partial_withdrawals"] == Decimal("500.00")
    # 28/06 e 29/06: o lote de 03/06 já tem IOF baixo e passa a ser o mais barato.
    assert details[date(2026, 6, 3)]["partial_withdrawals"] == Decimal("216.00")
    assert details[date(2026, 6, 11)]["partial_withdrawals"] == Decimal("0.00")


def test_gross_yield_includes_yield_already_withdrawn():
    details = _details()

    # Nubank: 66,17 e 22,10 de rendimento bruto nesses dois depósitos.
    assert Decimal("64") < details[date(2026, 6, 3)]["gross_yield"] < Decimal("68")
    assert Decimal("21") < details[date(2026, 6, 12)]["gross_yield"] < Decimal("23")


def test_iof_only_appears_on_deposits_withdrawn_before_30_days():
    details = _details()

    assert Decimal("0.2") < details[date(2026, 6, 3)]["iof"] < Decimal("0.4")  # Nubank: 0,31
    assert Decimal("0.4") < details[date(2026, 6, 12)]["iof"] < Decimal("0.9")  # Nubank: 0,55
    assert details[date(2026, 7, 2)]["iof"] == Decimal("0.00")


def test_reinvested_lot_replaces_original_in_deposit_details():
    start = date(2024, 1, 2)
    maturity = date(2026, 1, 1)
    rates = {start + timedelta(days=i): Decimal("0") for i in range((maturity - start).days + 1)}
    flows = [Flow(start, Decimal("1000"), sequence=0)]

    details = calculate_deposit_details(flows, rates, BASE, start, maturity)

    assert len(details) == 1
    assert details[0]["deposited_on"] == maturity
    assert details[0]["applied_amount"] == Decimal("1000.00")


def test_fully_withdrawn_lot_is_not_listed_in_deposit_details():
    start = date(2026, 6, 1)
    end = date(2026, 6, 2)
    rates = {start: Decimal("0"), end: Decimal("0")}
    flows = [
        Flow(start, Decimal("100"), sequence=0),
        Flow(end, Decimal("-100"), sequence=1),
    ]

    assert calculate_deposit_details(flows, rates, BASE, start, end) == []


def test_withdrawal_preserves_real_cent_residue_until_a_later_redemption():
    start = date(2026, 8, 16)
    withdrawal_day = date(2026, 9, 3)
    rates = {
        start + timedelta(days=i): Decimal("0.0534")
        for i in range((withdrawal_day - start).days + 1)
        if (start + timedelta(days=i)).weekday() < 5
    }
    flows = [
        Flow(start, Decimal("300"), sequence=0),
        Flow(withdrawal_day, Decimal("-301.13"), sequence=1),
    ]

    details = calculate_deposit_details(flows, rates, BASE, start, withdrawal_day)

    # Não apaga diferença de centavos por tolerância: um saldo pequeno pode
    # permanecer no RDB e ser resgatado em uma operação posterior.
    assert len(details) == 1
    assert details[0]["gross_balance"] == Decimal("0.05")


def test_same_day_deposit_details_keep_creation_order_not_amount_order():
    day = date(2026, 6, 1)
    rates = {day: Decimal("0")}
    flows = [
        Flow(day, Decimal("700"), sequence=0),
        Flow(day, Decimal("1000"), sequence=1),
    ]

    details = calculate_deposit_details(flows, rates, BASE, day, day)

    assert [item["applied_amount"] for item in details] == [
        Decimal("700.00"),
        Decimal("1000.00"),
    ]


def test_details_do_not_assign_earlier_same_day_withdrawal_to_later_deposit():
    day = date(2026, 6, 1)
    rates = {day: Decimal("0")}
    flows = [
        Flow(day, Decimal("-100"), sequence=0),
        Flow(day, Decimal("1000"), sequence=1),
    ]

    details = calculate_deposit_details(flows, rates, BASE, day, day)

    assert len(details) == 1
    assert details[0]["partial_withdrawals"] == Decimal("0.00")
