from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import CdiRate
from app.services import report_service


def test_goal_forecast_uses_recent_cdi_and_reports_assumptions(client, auth_headers, monkeypatch):
    today = date(2025, 1, 21)
    monkeypatch.setattr(report_service, "today_brazil", lambda: today)
    for day in range(15, 22):
        db.session.add(
            CdiRate(reference_date=date(2025, 1, day), daily_rate=Decimal("0.05"))
        )
    db.session.commit()

    account_response = client.post(
        "/api/accounts",
        json={
            "name": "Meta",
            "institution": "Nubank",
            "cdi_percent": "100.00",
            "opened_on": "2025-01-15",
            "goal_amount": "2000.00",
        },
        headers=auth_headers,
    )
    account_id = account_response.get_json()["account"]["id"]
    client.post(
        f"/api/accounts/{account_id}/transactions",
        json={"kind": "DEPOSIT", "amount": "1000.00", "occurred_on": "2025-01-15"},
        headers=auth_headers,
    )

    response = client.get(f"/api/accounts/{account_id}/goal-forecast", headers=auth_headers)

    assert response.status_code == 200
    forecast = response.get_json()["forecast"]
    assert forecast["status"] == "projected"
    assert forecast["months"] > 0
    assert forecast["projected_date"]
    assert "21 dias úteis por mês" in forecast["assumption"]
