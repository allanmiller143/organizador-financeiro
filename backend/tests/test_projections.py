import re
from decimal import Decimal

from app.services.projection_service import monthly_rate

BODY = {
    "initial_amount": "1000.00",
    "monthly_deposit": "0",
    "horizon_months": 12,
    "expected_cdi_annual": "12.00",
    "cdi_percent": "100",
}


def simulate(client, headers, **overrides):
    return client.post("/api/projections/simulate", json={**BODY, **overrides}, headers=headers)


def test_monthly_rate_compounds_back_to_the_annual_rate():
    rate = monthly_rate(Decimal("12"), Decimal("100"))

    assert abs((1 + rate) ** 12 - Decimal("1.12")) < Decimal("1e-15")


def test_monthly_rate_scales_with_cdi_percent():
    base = monthly_rate(Decimal("12"), Decimal("100"))

    assert monthly_rate(Decimal("12"), Decimal("110")) == base * Decimal("1.1")


def test_simulate_requires_token(client):
    response = client.post("/api/projections/simulate", json=BODY)

    assert response.status_code == 401


def test_simulate_one_year_matches_hand_calculation(client, auth_headers):
    response = simulate(client, auth_headers)

    assert response.status_code == 200
    body = response.get_json()["simulation"]
    assert len(body["months"]) == 12
    assert re.fullmatch(r"\d{4}-\d{2}", body["months"][0]["month"])
    summary = body["summary"]
    assert Decimal(summary["gross_balance"]) == Decimal("1120.00")  # 1000 a 12% ao ano
    assert Decimal(summary["gross_yield"]) == Decimal("120.00")
    assert Decimal(summary["tax_estimated"]) == Decimal("24.00")  # 360 dias: faixa de 20%
    assert Decimal(summary["net_balance"]) == Decimal("1096.00")
    assert body["depleted_month"] is None


def test_simulate_reports_when_money_runs_out(client, auth_headers):
    response = simulate(
        client,
        auth_headers,
        initial_amount="100.00",
        monthly_withdrawal="500.00",
        horizon_months=3,
    )

    assert response.status_code == 200
    assert response.get_json()["simulation"]["depleted_month"] == 1


def test_simulate_invalid_data_returns_422(client, auth_headers):
    response = simulate(client, auth_headers, horizon_months=0, monthly_deposit="-5")

    assert response.status_code == 422
    fields = {d["field"] for d in response.get_json()["error"]["details"]}
    assert {"horizon_months", "monthly_deposit"} <= fields