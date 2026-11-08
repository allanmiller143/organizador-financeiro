from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import CdiRate

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


def new_account(client, headers):
    return client.post("/api/accounts", json=ACCOUNT, headers=headers).get_json()["account"]["id"]


def transact(client, headers, account_id, kind, day, amount):
    return client.post(
        f"/api/accounts/{account_id}/transactions",
        json={"kind": kind, "amount": amount, "occurred_on": day},
        headers=headers,
    )


def history(client, headers, account_id):
    response = client.get(f"/api/accounts/{account_id}/transactions", headers=headers)
    return response.get_json()["transactions"]


def test_withdrawal_above_balance_is_blocked(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    transact(client, auth_headers, account_id, "DEPOSIT", "2025-01-15", "100.00")

    response = transact(client, auth_headers, account_id, "WITHDRAWAL", "2025-01-16", "5000.00")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "withdrawal_exceeds_balance"
    assert len(history(client, auth_headers, account_id)) == 1  # nada foi gravado


def test_withdrawal_can_use_earned_yield(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    transact(client, auth_headers, account_id, "DEPOSIT", "2025-01-15", "1000.00")

    # em 17/01 o saldo é 1000 x 1,01 x 1,01 = 1020,10: mais do que foi aportado
    response = transact(client, auth_headers, account_id, "WITHDRAWAL", "2025-01-17", "1020.10")

    assert response.status_code == 201


def test_deleting_a_deposit_that_supports_a_withdrawal_is_blocked(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    deposit = transact(client, auth_headers, account_id, "DEPOSIT", "2025-01-15", "1000.00")
    transact(client, auth_headers, account_id, "WITHDRAWAL", "2025-01-16", "500.00")

    response = client.delete(
        f"/api/transactions/{deposit.get_json()['transaction']['id']}", headers=auth_headers
    )

    assert response.status_code == 422
    assert len(history(client, auth_headers, account_id)) == 2


def test_raising_a_withdrawal_amount_is_blocked(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    transact(client, auth_headers, account_id, "DEPOSIT", "2025-01-15", "1000.00")
    withdrawal = transact(client, auth_headers, account_id, "WITHDRAWAL", "2025-01-16", "500.00")

    response = client.patch(
        f"/api/transactions/{withdrawal.get_json()['transaction']['id']}",
        json={"amount": "5000.00"},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert Decimal(history(client, auth_headers, account_id)[0]["amount"]) == Decimal("500.00")
    