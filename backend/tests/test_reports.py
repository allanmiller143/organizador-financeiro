import uuid
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import CdiRate, Transaction, TransactionKind

ACCOUNT = {
    "name": "Reserva",
    "institution": "Nubank",
    "cdi_percent": "100.00",
    "opened_on": "2025-01-15",
}


def add_cdi(*days):
    """Grava CDI fictício de 1% ao dia nos dias de janeiro de 2025 informados."""
    for day in days:
        db.session.add(CdiRate(reference_date=date(2025, 1, day), daily_rate=Decimal("1")))
    db.session.commit()


def new_account(client, headers):
    response = client.post("/api/accounts", json=ACCOUNT, headers=headers)
    return response.get_json()["account"]["id"]


def deposit(client, headers, account_id, day, amount="1000.00"):
    return client.post(
        f"/api/accounts/{account_id}/transactions",
        json={"kind": "DEPOSIT", "amount": amount, "occurred_on": day},
        headers=headers,
    )


def get_summary(client, headers, account_id):
    return client.get(f"/api/accounts/{account_id}/summary", headers=headers)


def test_summary_gross_tax_and_net(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15")

    response = get_summary(client, auth_headers, account_id)

    assert response.status_code == 200
    body = response.get_json()["summary"]
    assert body["as_of"] == "2025-01-21"
    assert Decimal(body["gross_balance"]) == Decimal("1040.60")  # 1000 x 1,01^4
    assert Decimal(body["invested"]) == Decimal("1000.00")
    assert Decimal(body["gross_yield"]) == Decimal("40.60")
    assert Decimal(body["tax_estimated"]) == Decimal("9.14")  # 22,5% do rendimento
    assert Decimal(body["net_balance"]) == Decimal("1031.47")
    assert Decimal(body["tax_paid"]) == Decimal("0.00")


def test_empty_account_summary_is_zero(client, auth_headers):
    add_cdi(15, 16, 17)
    account_id = new_account(client, auth_headers)

    response = get_summary(client, auth_headers, account_id)

    assert response.status_code == 200
    assert Decimal(response.get_json()["summary"]["gross_balance"]) == 0


def test_summary_without_cdi_returns_409(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = get_summary(client, auth_headers, account_id)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "cdi_not_synced"


def test_summary_with_incomplete_cdi_returns_409(client, auth_headers):
    add_cdi(21)  # o CDI só começa 6 dias depois do aporte
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15")

    response = get_summary(client, auth_headers, account_id)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "cdi_incomplete"


def test_summary_with_withdrawal_above_balance_returns_409(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15", "100.00")
    db.session.add(  # direto no banco, como se a regra de bloqueio não existisse
        Transaction(
            account_id=uuid.UUID(account_id),
            kind=TransactionKind.WITHDRAWAL,
            amount=Decimal("5000.00"),
            occurred_on=date(2025, 1, 16),
        )
    )
    db.session.commit()

    response = get_summary(client, auth_headers, account_id)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "insufficient_balance"


def test_cannot_see_other_users_summary(client, auth_headers, other_headers):
    add_cdi(15, 16)
    other_account_id = new_account(client, other_headers)

    response = get_summary(client, auth_headers, other_account_id)

    assert response.status_code == 404


def test_summary_requires_token(client):
    response = client.get(f"/api/accounts/{uuid.uuid4()}/summary")

    assert response.status_code == 401


def test_monthly_yields(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15")

    response = client.get(
        f"/api/accounts/{account_id}/monthly-yields", headers=auth_headers
    )

    assert response.status_code == 200
    months = response.get_json()["monthly_yields"]["months"]
    assert len(months) == 1
    assert months[0]["month"] == "2025-01"
    assert Decimal(months[0]["yield_amount"]) == Decimal("40.60")