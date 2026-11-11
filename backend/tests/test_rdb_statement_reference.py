"""Referência de resgates por lote extraída do extrato RDB real do Nubank."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import app.services.withdrawal_allocator as allocator
from app.services.deposit_detail_service import calculate_deposit_details
from app.services.yield_engine import Flow

D = Decimal
FIXTURES = Path(__file__).parent / "fixtures"


def _flows():
    # A ordem de 29/09 é a ordem cronológica confirmada pelo usuário:
    # o aporte que aparece mais abaixo no PDF é o mais antigo.
    rows = [
        ("2026-08-16", "a", "300.00"),
        ("2026-09-03", "r", "301.13"),
        ("2026-09-04", "a", "1000.00"),
        ("2026-09-09", "r", "290.00"),
        ("2026-09-11", "r", "666.00"),
        ("2026-09-18", "a", "1500.00"),
        ("2026-09-20", "r", "1500.00"),
        ("2026-09-29", "a", "500.00"),
        ("2026-09-29", "a", "621.00"),
        ("2026-09-29", "a", "30.00"),
        ("2026-09-29", "a", "300.00"),
        ("2026-09-29", "a", "5.00"),
        ("2026-10-03", "a", "1500.00"),
        ("2026-10-14", "a", "3000.00"),
        ("2026-10-18", "r", "1000.00"),
        ("2026-10-28", "r", "422.00"),
        ("2026-11-04", "a", "2300.00"),
        ("2026-11-04", "r", "1500.00"),
        ("2026-11-06", "a", "2100.00"),
    ]
    flows = [
        Flow(
            date.fromisoformat(day),
            D(amount) if kind == "a" else -D(amount),
            D("120.00"),
            24,
            False,
            sequence,
        )
        for sequence, (day, kind, amount) in enumerate(rows)
    ]
    source = {sequence: (date.fromisoformat(day), kind, D(amount)) for sequence, (day, kind, amount) in enumerate(rows)}
    return flows, source


def _rates():
    raw = json.loads((FIXTURES / "cdi_2026_reference.json").read_text())
    return {
        datetime.strptime(row["data"], "%d/%m/%Y").date(): D(row["valor"])
        for row in raw
    }


def test_real_rdb_statement_withdrawal_allocations_match_per_lot(monkeypatch):
    flows, source = _flows()
    original = allocator.allocate_withdrawal
    observed = []

    def recording_allocator(lots, net_amount, day, sequence=None, **kwargs):
        allocations = original(lots, net_amount, day, sequence, **kwargs)
        observed.extend(
            (
                day,
                source[item.lot.sequence],
                item.gross_amount,
                item.income_tax,
                item.iof,
                item.net_amount,
            )
            for item in allocations
        )
        return allocations

    monkeypatch.setattr(allocator, "allocate_withdrawal", recording_allocator)
    details = calculate_deposit_details(
        flows,
        _rates(),
        D("120.00"),
        date(2026, 8, 16),
        date(2026, 11, 6),
    )

    def rows_on(day):
        return [row for row in observed if row[0] == date.fromisoformat(day)]

    # 03/09: o arredondamento deixa R$ 0,01 no lote, resgatado em 09/09.
    assert rows_on("2026-09-03") == [
        (date(2026, 9, 3), (date(2026, 8, 16), "a", D("300.00")), D("302.42"), D("0.32"), D("0.97"), D("301.13"))
    ]
    assert [(r[2], r[3], r[4], r[5]) for r in rows_on("2026-09-09")] == [
        (D("0.01"), D("0.00"), D("0.00"), D("0.01")),
        (D("290.29"), D("0.01"), D("0.29"), D("289.99")),
    ]
    assert [(r[2], r[3], r[4], r[5]) for r in rows_on("2026-09-11")] == [
        (D("667.33"), D("0.08"), D("1.25"), D("666.00"))
    ]

    # O lote de R$ 1.500 deixa R$ 0,05 após o resgate de 20/09; esse centavo
    # residual reaparece no extrato junto ao resgate de 18/10.
    assert [(r[2], r[3], r[4], r[5]) for r in rows_on("2026-09-20")] == [
        (D("1500.86"), D("0.01"), D("0.85"), D("1500.00"))
    ]
    assert [(r[2], r[3], r[4], r[5]) for r in rows_on("2026-10-18")] == [
        (D("0.05"), D("0.00"), D("0.00"), D("0.05")),
        (D("1001.57"), D("0.05"), D("1.57"), D("999.95")),
    ]

    # 28/10: R$ 5 e R$ 30 são encerrados; o lote de R$ 621 sofre o parcial
    # de R$ 386,67, e o de R$ 300 permanece intacto.
    assert [(r[1][2], r[2], r[3], r[4], r[5]) for r in rows_on("2026-10-28")] == [
        (D("5.00"), D("5.06"), D("0.01"), D("0.00"), D("5.05")),
        (D("30.00"), D("30.37"), D("0.08"), D("0.01"), D("30.28")),
        (D("621.00"), D("387.83"), D("1.02"), D("0.14"), D("386.67")),
    ]
    assert sum((r[5] for r in rows_on("2026-10-28")), D("0")) == D("422.00")

    active = {item["applied_amount"]: item for item in details}
    assert active[D("300.00")]["partial_withdrawals"] == D("0.00")
    assert active[D("500.00")]["partial_withdrawals"] == D("0.00")
    assert active[D("621.00")]["partial_withdrawals"] == D("386.67")
    assert D("5.00") not in active and D("30.00") not in active
    assert active[D("3000.00")]["partial_withdrawals"] == D("999.95")

    # No imposto na saída do aporte de mesmo dia em 04/11.
    assert [(r[2], r[3], r[4], r[5]) for r in rows_on("2026-11-04")] == [
        (D("1500.00"), D("0.00"), D("0.00"), D("1500.00"))
    ]
