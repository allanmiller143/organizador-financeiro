from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import CdiRate
from app.services import report_service


def test_matured_lot_reinvests_today_without_published_rate(client, auth_headers, monkeypatch):
    today = date(2026, 11, 11)
    start = date(2024, 11, 11)
    monkeypatch.setattr(report_service, "today_brazil", lambda: today)

    account_response = client.post(
        "/api/accounts",
        json={
            "name": "Vencimento",
            "institution": "Nubank",
            "cdi_percent": "100.00",
            "opened_on": start.isoformat(),
        },
        headers=auth_headers,
    )
    account_id = account_response.get_json()["account"]["id"]
    deposit_response = client.post(
        f"/api/accounts/{account_id}/transactions",
        json={"kind": "DEPOSIT", "amount": "1000.00", "occurred_on": start.isoformat()},
        headers=auth_headers,
    )
    assert deposit_response.status_code == 201

    day = start
    while day < today:
        if day.weekday() < 5:
            db.session.add(CdiRate(reference_date=day, daily_rate=Decimal("0")))
        day += timedelta(days=1)
    db.session.commit()

    response = client.get(f"/api/accounts/{account_id}/monthly-yields", headers=auth_headers)

    assert response.status_code == 200
    months = response.get_json()["monthly_yields"]["months"]
    events = [event for month in months for event in month["reapplications"]]
    assert len(events) == 1
    assert events[0]["occurred_on"] == today.isoformat()
    assert Decimal(events[0]["amount"]) == Decimal("1000.00")
