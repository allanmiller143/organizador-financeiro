import uuid
from datetime import date
from decimal import Decimal

from app.errors import AppError
from app.extensions import db
from app.models import CdiRate
from app.services import cdi_service

ACCOUNT = {
    "name": "Reserva",
    "institution": "Nubank",
    "cdi_percent": "100.00",
    "opened_on": "2025-01-15",
}


def add_cdi(*days):
    for day in days:
        db.session.add(CdiRate(reference_date=date(2025, 1, day), daily_rate=Decimal("1")))
    db.session.commit()


def new_account(client, headers, name="Reserva"):
    response = client.post("/api/accounts", json={**ACCOUNT, "name": name}, headers=headers)
    return response.get_json()["account"]["id"]


def deposit(client, headers, account_id, amount):
    return client.post(
        f"/api/accounts/{account_id}/transactions",
        json={"kind": "DEPOSIT", "amount": amount, "occurred_on": "2025-01-15"},
        headers=headers,
    )


def get_dashboard(client, headers):
    return client.get("/api/dashboard", headers=headers)


def test_dashboard_totals_and_shares(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    a = new_account(client, auth_headers, "A")
    b = new_account(client, auth_headers, "B")
    deposit(client, auth_headers, a, "1000.00")
    deposit(client, auth_headers, b, "3000.00")

    response = get_dashboard(client, auth_headers)

    assert response.status_code == 200
    body = response.get_json()["dashboard"]
    assert body["as_of"] == "2025-01-21"
    assert Decimal(body["totals"]["gross_balance"]) == Decimal("4162.42")  # 4000 x 1,01^4
    assert Decimal(body["totals"]["invested"]) == Decimal("4000.00")
    shares = {acc["name"]: Decimal(acc["share_percent"]) for acc in body["accounts"]}
    assert shares == {"A": Decimal("25.00"), "B": Decimal("75.00")}


def test_dashboard_without_accounts_is_empty(client, auth_headers):
    response = get_dashboard(client, auth_headers)

    assert response.status_code == 200
    body = response.get_json()["dashboard"]
    assert body["accounts"] == []
    assert body["as_of"] is None
    assert Decimal(body["totals"]["gross_balance"]) == 0


def test_dashboard_only_counts_own_accounts(client, auth_headers, other_headers):
    add_cdi(15, 16, 17, 20, 21)
    mine = new_account(client, auth_headers, "Minha")
    theirs = new_account(client, other_headers, "Deles")
    deposit(client, auth_headers, mine, "1000.00")
    deposit(client, other_headers, theirs, "9000.00")

    response = get_dashboard(client, auth_headers)

    body = response.get_json()["dashboard"]
    assert [acc["name"] for acc in body["accounts"]] == ["Minha"]
    assert Decimal(body["totals"]["gross_balance"]) == Decimal("1040.60")


def test_dashboard_without_cdi_returns_409(client, auth_headers):
    new_account(client, auth_headers)

    response = get_dashboard(client, auth_headers)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "cdi_not_synced"


def test_dashboard_requires_token(client):
    assert client.get("/api/dashboard").status_code == 401


def test_dashboard_syncs_stale_cdi(app, client, auth_headers, monkeypatch):
    app.config["CDI_AUTO_SYNC"] = True
    calls = []

    def fake_fetch(start, end):
        calls.append((start, end))
        return []

    monkeypatch.setattr(cdi_service, "fetch_cdi_series", fake_fetch)
    add_cdi(15)  # CDI de janeiro de 2025: muito atrasado
    new_account(client, auth_headers)

    response = get_dashboard(client, auth_headers)

    assert response.status_code == 200
    assert len(calls) >= 1
    assert calls[0][0] == date(2025, 1, 16)  # continua do dia seguinte ao último


def test_dashboard_works_when_cdi_source_is_down(app, client, auth_headers, monkeypatch):
    app.config["CDI_AUTO_SYNC"] = True

    def broken_fetch(start, end):
        raise AppError("fora do ar", 502, "cdi_source_unavailable")

    monkeypatch.setattr(cdi_service, "fetch_cdi_series", broken_fetch)
    add_cdi(15, 16)
    new_account(client, auth_headers)

    response = get_dashboard(client, auth_headers)

    assert response.status_code == 200


def archive(client, headers, account_id):
    return client.patch(
        f"/api/accounts/{account_id}", json={"is_active": False}, headers=headers
    )


def test_dashboard_ignores_archived_accounts(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    a = new_account(client, auth_headers, "A")
    b = new_account(client, auth_headers, "B")
    deposit(client, auth_headers, a, "1000.00")
    deposit(client, auth_headers, b, "3000.00")
    archive(client, auth_headers, b)

    body = get_dashboard(client, auth_headers).get_json()["dashboard"]

    assert [acc["name"] for acc in body["accounts"]] == ["A"]
    assert Decimal(body["totals"]["gross_balance"]) == Decimal("1040.60")


def test_archived_account_still_has_its_own_summary(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    a = new_account(client, auth_headers, "A")
    deposit(client, auth_headers, a, "1000.00")
    archive(client, auth_headers, a)

    response = client.get(f"/api/accounts/{a}/summary", headers=auth_headers)

    assert response.status_code == 200
    assert Decimal(response.get_json()["summary"]["gross_balance"]) == Decimal("1040.60")