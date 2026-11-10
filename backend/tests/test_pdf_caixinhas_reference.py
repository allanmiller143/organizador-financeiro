"""Regressão baseada no documento corrigido CaixinhasNubank—dadoscorrigidos.pdf.

A caixinha 2 é o controle: o motor original já reproduz seus saques parciais e
não pode ser alterado ao calibrar os casos de arredondamento da caixinha 1/3.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.services.deposit_detail_service import calculate_deposit_details
from app.services.yield_engine import Flow

D = Decimal
FIXTURES = Path(__file__).parent / "fixtures"


def _cdi_rates():
    raw = json.loads((FIXTURES / "cdi_2026_reference.json").read_text())
    return {
        datetime.strptime(row["data"], "%d/%m/%Y").date(): D(row["valor"])
        for row in raw
    }


def _caixinha_2_flows():
    # Extraído do histórico da caixinha 2 (120% CDI) no PDF corrigido.
    rows = [
        ("2026-06-03", "aporte", "1125.00"),
        ("2026-06-11", "aporte", "2750.00"),
        ("2026-06-12", "aporte", "825.00"),
        ("2026-06-16", "retirada", "500.00"),
        ("2026-06-28", "retirada", "16.00"),
        ("2026-06-29", "retirada", "200.00"),
        ("2026-07-02", "aporte", "1000.00"),
        ("2026-07-10", "aporte", "3000.00"),
        ("2026-08-03", "aporte", "510.00"),
        ("2026-08-16", "aporte", "1354.32"),
    ]
    return [
        Flow(
            date.fromisoformat(day),
            D(value) if kind == "aporte" else -D(value),
            cdi_percent=D("120.00"),
            sequence=index,
        )
        for index, (day, kind, value) in enumerate(rows)
    ]


def test_original_engine_preserves_pdf_caixinha_2_withdrawal_allocation():
    flows = _caixinha_2_flows()
    details = calculate_deposit_details(
        flows,
        _cdi_rates(),
        D("120.00"),
        date(2026, 6, 1),
        date(2026, 11, 9),
    )
    by_applied = {item["applied_amount"]: item for item in details}

    # PDF: os R$ 500 saem do lote de 12/06; os R$ 216 (16 + 200) saem do lote
    # de 03/06. Mantém tolerância de centavos apenas nos impostos arredondados.
    assert by_applied[D("825.00")]["partial_withdrawals"] == D("500.00")
    assert by_applied[D("1125.00")]["partial_withdrawals"] == D("216.00")
    assert by_applied[D("2750.00")]["partial_withdrawals"] == D("0.00")
    assert by_applied[D("1000.00")]["partial_withdrawals"] == D("0.00")
    assert by_applied[D("3000.00")]["partial_withdrawals"] == D("0.00")
    assert by_applied[D("510.00")]["partial_withdrawals"] == D("0.00")
    assert by_applied[D("1354.32")]["partial_withdrawals"] == D("0.00")

    # Valores publicados no PDF; as diferenças de 1 centavo em IR são de
    # arredondamento do valor exibido, não de seleção do lote.
    assert by_applied[D("1125.00")]["gross_yield"] == D("66.17")
    assert by_applied[D("825.00")]["gross_yield"] == D("22.10")
    assert by_applied[D("510.00")]["gross_yield"] == D("21.44")
    assert by_applied[D("1354.32")]["gross_yield"] == D("48.18")
    assert abs(by_applied[D("825.00")]["income_tax"] - D("4.84")) <= D("0.01")
    assert by_applied[D("825.00")]["iof"] == D("0.55")
