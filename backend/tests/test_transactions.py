from decimal import Decimal

ACCOUNT = {
    "name": "Reserva",
    "institution": "Nubank",
    "cdi_percent": "100.00",
    "opened_on": "2025-01-15",
}
TX = {
    "kind": "DEPOSIT",
    "amount": "1000.00",
    "occurred_on": "2025-02-10",
    "note": "Primeiro aporte",
}


def new_account(client, headers):
    response = client.post("/api/accounts", json=ACCOUNT, headers=headers)
    return response.get_json()["account"]["id"]


def add(client, headers, account_id, **overrides):
    return client.post(
        f"/api/accounts/{account_id}/transactions",
        json={**TX, **overrides},
        headers=headers,
    )


def listing(client, headers, account_id, query=""):
    return client.get(f"/api/accounts/{account_id}/transactions{query}", headers=headers)


def test_create_deposit(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(client, auth_headers, account_id)

    assert response.status_code == 201
    body = response.get_json()["transaction"]
    assert body["kind"] == "DEPOSIT"
    assert Decimal(body["amount"]) == Decimal("1000.00")
    assert body["account_id"] == account_id


def test_create_withdrawal(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(client, auth_headers, account_id, kind="WITHDRAWAL", amount="200.50")

    assert response.status_code == 201
    body = response.get_json()["transaction"]
    assert body["kind"] == "WITHDRAWAL"
    assert Decimal(body["amount"]) == Decimal("200.50")


def test_invalid_amount_returns_422(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(client, auth_headers, account_id, amount="0")

    assert response.status_code == 422
    fields = {d["field"] for d in response.get_json()["error"]["details"]}
    assert "amount" in fields


def test_future_date_returns_422(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(client, auth_headers, account_id, occurred_on="2999-01-01")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "date_in_future"


def test_date_before_opening_returns_422(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(client, auth_headers, account_id, occurred_on="2025-01-01")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "date_before_opening"


def test_create_requires_token(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = client.post(f"/api/accounts/{account_id}/transactions", json=TX)

    assert response.status_code == 401


def test_cannot_add_to_other_users_account(client, auth_headers, other_headers):
    other_account_id = new_account(client, other_headers)

    response = add(client, auth_headers, other_account_id)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "account_not_found"


def test_list_newest_first(client, auth_headers):
    account_id = new_account(client, auth_headers)
    add(client, auth_headers, account_id, occurred_on="2025-02-10")
    add(client, auth_headers, account_id, occurred_on="2025-03-10")

    response = listing(client, auth_headers, account_id)

    dates = [t["occurred_on"] for t in response.get_json()["transactions"]]
    assert dates == ["2025-03-10", "2025-02-10"]


def test_same_day_transactions_keep_registration_order(client, auth_headers):
    account_id = new_account(client, auth_headers)
    first = add(client, auth_headers, account_id, amount="840.00").get_json()["transaction"]
    second = add(client, auth_headers, account_id, amount="160.00").get_json()["transaction"]

    response = listing(client, auth_headers, account_id)
    same_day = [
        item for item in response.get_json()["transactions"] if item["occurred_on"] == TX["occurred_on"]
    ]

    assert [item["id"] for item in same_day[:2]] == [first["id"], second["id"]]


def test_reorder_same_day_preserves_mixed_deposit_withdrawal_order(client, auth_headers):
    account_id = new_account(client, auth_headers)
    deposit = add(client, auth_headers, account_id, amount="1000.00").get_json()["transaction"]
    withdrawal = add(
        client,
        auth_headers,
        account_id,
        kind="WITHDRAWAL",
        amount="100.00",
    ).get_json()["transaction"]

    response = client.patch(
        f"/api/accounts/{account_id}/transactions/order",
        json={"transaction_ids": [withdrawal["id"], deposit["id"]]},
        headers=auth_headers,
    )

    assert response.status_code == 204
    same_day = listing(client, auth_headers, account_id).get_json()["transactions"]
    assert [item["id"] for item in same_day[:2]] == [withdrawal["id"], deposit["id"]]


def test_list_filters_by_kind(client, auth_headers):
    account_id = new_account(client, auth_headers)
    add(client, auth_headers, account_id)
    add(client, auth_headers, account_id, kind="WITHDRAWAL", amount="50.00")

    response = listing(client, auth_headers, account_id, "?kind=WITHDRAWAL")

    kinds = [t["kind"] for t in response.get_json()["transactions"]]
    assert kinds == ["WITHDRAWAL"]


def test_list_filters_by_date_range(client, auth_headers):
    account_id = new_account(client, auth_headers)
    for day in ("2025-01-20", "2025-02-10", "2025-03-10"):
        add(client, auth_headers, account_id, occurred_on=day)

    response = listing(
        client, auth_headers, account_id, "?date_from=2025-02-01&date_to=2025-02-28"
    )

    dates = [t["occurred_on"] for t in response.get_json()["transactions"]]
    assert dates == ["2025-02-10"]


def test_list_invalid_range_returns_422(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = listing(
        client, auth_headers, account_id, "?date_from=2025-03-01&date_to=2025-02-01"
    )

    assert response.status_code == 422


def test_cannot_list_other_users_account(client, auth_headers, other_headers):
    other_account_id = new_account(client, other_headers)

    response = listing(client, auth_headers, other_account_id)

    assert response.status_code == 404


def test_update_amount(client, auth_headers):
    account_id = new_account(client, auth_headers)
    tx_id = add(client, auth_headers, account_id).get_json()["transaction"]["id"]

    response = client.patch(
        f"/api/transactions/{tx_id}",
        json={
            "amount": "1500.00",
            "occurred_on": "2025-03-10",
            "note": "Corrigido",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    updated = response.get_json()["transaction"]
    assert Decimal(updated["amount"]) == Decimal("1500.00")
    assert updated["occurred_on"] == "2025-03-10"
    assert updated["note"] == "Corrigido"


def test_update_date_is_validated_again(client, auth_headers):
    account_id = new_account(client, auth_headers)
    tx_id = add(client, auth_headers, account_id).get_json()["transaction"]["id"]

    response = client.patch(
        f"/api/transactions/{tx_id}",
        json={"occurred_on": "2025-01-01"},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "date_before_opening"


def test_cannot_update_other_users_transaction(client, auth_headers, other_headers):
    other_account_id = new_account(client, other_headers)
    tx_id = add(client, other_headers, other_account_id).get_json()["transaction"]["id"]

    response = client.patch(
        f"/api/transactions/{tx_id}", json={"amount": "1.00"}, headers=auth_headers
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "transaction_not_found"


def test_delete_transaction(client, auth_headers):
    account_id = new_account(client, auth_headers)
    tx_id = add(client, auth_headers, account_id).get_json()["transaction"]["id"]

    response = client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)

    assert response.status_code == 204
    assert listing(client, auth_headers, account_id).get_json()["transactions"] == []


def test_cannot_delete_other_users_transaction(client, auth_headers, other_headers):
    other_account_id = new_account(client, other_headers)
    tx_id = add(client, other_headers, other_account_id).get_json()["transaction"]["id"]

    response = client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)

    assert response.status_code == 404
    still_there = listing(client, other_headers, other_account_id).get_json()
    assert len(still_there["transactions"]) == 1


def new_account_with(client, headers, cdi_percent):
    response = client.post(
        "/api/accounts", json={**ACCOUNT, "cdi_percent": cdi_percent}, headers=headers
    )
    return response.get_json()["account"]["id"]


def test_locked_deposit_is_allowed_on_a_100_percent_account(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(
        client, auth_headers, account_id, cdi_percent="104.50", term_months=6, locked=True
    )

    assert response.status_code == 201
    body = response.get_json()["transaction"]
    assert body["locked"] is True
    assert Decimal(body["cdi_percent"]) == Decimal("104.50")
    assert body["term_months"] == 6


def test_locked_deposit_is_rejected_above_100_percent(client, auth_headers):
    account_id = new_account_with(client, auth_headers, "120.00")

    response = add(
        client, auth_headers, account_id, cdi_percent="104.50", term_months=6, locked=True
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "lock_not_allowed"


def test_lock_longer_than_two_years_is_rejected(client, auth_headers):
    account_id = new_account(client, auth_headers)

    response = add(
        client, auth_headers, account_id, cdi_percent="106.00", term_months=36, locked=True
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "lock_term_too_long"


def test_unlocked_deposit_takes_the_account_percentage(client, auth_headers):
    account_id = new_account_with(client, auth_headers, "120.00")

    response = add(client, auth_headers, account_id, cdi_percent="100.00")

    assert response.status_code == 201
    body = response.get_json()["transaction"]
    assert body["locked"] is False
    assert Decimal(body["cdi_percent"]) == Decimal("120.00")
