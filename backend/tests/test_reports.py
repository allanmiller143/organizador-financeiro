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


def test_today_deposit_counts_before_interest_update_and_can_be_withdrawn(
    client, auth_headers, monkeypatch
):
    from app.services import report_service, transaction_service

    today = date(2025, 1, 21)
    monkeypatch.setattr(report_service, "today_brazil", lambda: today)
    monkeypatch.setattr(transaction_service, "today_brazil", lambda: today)
    add_cdi(15, 16, 17, 20)  # último rendimento calculado: ontem
    account_id = new_account(client, auth_headers)

    aporte = deposit(client, auth_headers, account_id, today.isoformat(), "500.00")
    assert aporte.status_code == 201
    after_deposit = get_summary(client, auth_headers, account_id).get_json()["summary"]
    assert after_deposit["as_of"] == "2025-01-20"
    assert Decimal(after_deposit["gross_balance"]) == Decimal("500.00")

    retirada = client.post(
        f"/api/accounts/{account_id}/transactions",
        json={
            "kind": "WITHDRAWAL",
            "amount": "5.00",
            "occurred_on": today.isoformat(),
        },
        headers=auth_headers,
    )
    assert retirada.status_code == 201
    after_withdrawal = get_summary(client, auth_headers, account_id).get_json()["summary"]
    assert after_withdrawal["as_of"] == "2025-01-20"
    assert Decimal(after_withdrawal["gross_balance"]) == Decimal("495.00")


def test_summary_gross_tax_and_net(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15")

    response = get_summary(client, auth_headers, account_id)

    assert response.status_code == 200
    body = response.get_json()["summary"]
    assert body["as_of"] == "2025-01-21"
    assert Decimal(body["gross_balance"]) == Decimal("1051.01")  # 1000 x 1,01^4: o dia do depósito (15/01) não rende
    assert Decimal(body["invested"]) == Decimal("1000.00")
    assert Decimal(body["gross_yield"]) == Decimal("51.01")
    # idade de 6 dias: IOF de 80% do rendimento e IR de 22,5% sobre o que sobra
    assert Decimal(body["iof_estimated"]) == Decimal("40.81")
    assert Decimal(body["tax_estimated"]) == Decimal("43.10")  # IOF 32,48 + IR 1,83
    assert Decimal(body["net_balance"]) == Decimal("1007.91")
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
    assert Decimal(months[0]["yield_amount"]) == Decimal("51.01")
    assert Decimal(months[0]["net_yield_amount"]) == Decimal("7.91")
    assert Decimal(months[0]["gross_balance"]) == Decimal("1051.01")
    assert Decimal(months[0]["net_balance"]) == Decimal("1007.91")
    assert months[0]["reapplications"] == []


def test_history_csv_is_simple_day_operation_value(client, auth_headers):
    add_cdi(15, 16, 17, 20, 21)
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15", "100.00")
    client.post(
        f"/api/accounts/{account_id}/transactions",
        json={"kind": "WITHDRAWAL", "amount": "20.00", "occurred_on": "2025-01-16"},
        headers=auth_headers,
    )

    response = client.get(f"/api/accounts/{account_id}/history.csv", headers=auth_headers)

    assert response.status_code == 200
    rows = response.data.decode("utf-8-sig").strip().splitlines()
    assert rows[0] == "dia;operacao;valor"
    assert rows[1].split(";") == ["2025-01-16", "retirada", "20.00"]
    assert rows[2].split(";") == ["2025-01-15", "aporte", "100.00"]


def test_history_csv_preserves_manual_same_day_order(client, auth_headers):
    add_cdi(15)
    account_id = new_account(client, auth_headers)
    first = deposit(client, auth_headers, account_id, "2025-01-15", "100.00").get_json()["transaction"]["id"]
    second = deposit(client, auth_headers, account_id, "2025-01-15", "200.00").get_json()["transaction"]["id"]
    response = client.patch(
        f"/api/accounts/{account_id}/transactions/order",
        json={"transaction_ids": [second, first]},
        headers=auth_headers,
    )
    assert response.status_code == 204

    csv_response = client.get(f"/api/accounts/{account_id}/history.csv", headers=auth_headers)
    rows = csv_response.data.decode("utf-8-sig").strip().splitlines()
    assert rows[1].split(";") == ["2025-01-15", "aporte", "200.00"]
    assert rows[2].split(";") == ["2025-01-15", "aporte", "100.00"]


def test_new_same_day_transactions_appear_in_registration_order(client, auth_headers):
    add_cdi(15)
    account_id = new_account(client, auth_headers)
    deposit(client, auth_headers, account_id, "2025-01-15", "100.00")
    deposit(client, auth_headers, account_id, "2025-01-15", "200.00")
    deposit(client, auth_headers, account_id, "2025-01-15", "300.00")

    response = client.get(f"/api/accounts/{account_id}/transactions", headers=auth_headers)
    assert [row["amount"] for row in response.get_json()["transactions"]] == [
        "100.00",
        "200.00",
        "300.00",
    ]
