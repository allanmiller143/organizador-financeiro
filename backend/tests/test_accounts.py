from decimal import Decimal

ACCOUNT = {
    "name": "Reserva de emergência",
    "institution": "Nubank",
    "cdi_percent": "100.00",
    "opened_on": "2025-01-15",
}


def create(client, headers, **overrides):
    return client.post("/api/accounts", json={**ACCOUNT, **overrides}, headers=headers)


def test_create_account(client, auth_headers):
    response = create(client, auth_headers)

    assert response.status_code == 201
    body = response.get_json()["account"]
    assert body["name"] == ACCOUNT["name"]
    assert Decimal(body["cdi_percent"]) == Decimal("100")
    assert body["is_active"] is True
    assert body["goal_amount"] is None


def test_create_and_update_account_goal(client, auth_headers):
    account_id = create(client, auth_headers, goal_amount="2500.00").get_json()["account"]["id"]

    response = client.get(f"/api/accounts/{account_id}", headers=auth_headers)
    assert Decimal(response.get_json()["account"]["goal_amount"]) == Decimal("2500.00")

    response = client.patch(
        f"/api/accounts/{account_id}", json={"goal_amount": "3000.00"}, headers=auth_headers
    )
    assert Decimal(response.get_json()["account"]["goal_amount"]) == Decimal("3000.00")

    response = client.patch(
        f"/api/accounts/{account_id}", json={"goal_amount": None}, headers=auth_headers
    )
    assert response.get_json()["account"]["goal_amount"] is None


def test_create_requires_token(client):
    response = client.post("/api/accounts", json=ACCOUNT)

    assert response.status_code == 401


def test_create_invalid_returns_422(client, auth_headers):
    response = create(client, auth_headers, cdi_percent="-5", name="")

    assert response.status_code == 422
    fields = {d["field"] for d in response.get_json()["error"]["details"]}
    assert {"cdi_percent", "name"} <= fields


def test_list_returns_only_my_accounts(client, auth_headers, other_headers):
    create(client, auth_headers, name="Minha")
    create(client, other_headers, name="De outra pessoa")

    response = client.get("/api/accounts", headers=auth_headers)

    names = [a["name"] for a in response.get_json()["accounts"]]
    assert names == ["Minha"]


def test_get_other_users_account_returns_404(client, auth_headers, other_headers):
    account_id = create(client, other_headers).get_json()["account"]["id"]

    response = client.get(f"/api/accounts/{account_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "account_not_found"


def test_update_name(client, auth_headers):
    account_id = create(client, auth_headers).get_json()["account"]["id"]

    response = client.patch(
        f"/api/accounts/{account_id}", json={"name": "Novo nome"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.get_json()["account"]["name"] == "Novo nome"


def test_cdi_percent_cannot_be_changed(client, auth_headers):
    account_id = create(client, auth_headers).get_json()["account"]["id"]

    response = client.patch(
        f"/api/accounts/{account_id}", json={"cdi_percent": "120"}, headers=auth_headers
    )

    assert response.status_code == 422


def test_cannot_update_other_users_account(client, auth_headers, other_headers):
    account_id = create(client, other_headers).get_json()["account"]["id"]

    response = client.patch(
        f"/api/accounts/{account_id}", json={"name": "Invadida"}, headers=auth_headers
    )

    assert response.status_code == 404


def test_delete_account(client, auth_headers):
    account_id = create(client, auth_headers).get_json()["account"]["id"]

    response = client.delete(f"/api/accounts/{account_id}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(f"/api/accounts/{account_id}", headers=auth_headers).status_code == 404


def test_cannot_delete_other_users_account(client, auth_headers, other_headers):
    account_id = create(client, other_headers).get_json()["account"]["id"]

    response = client.delete(f"/api/accounts/{account_id}", headers=auth_headers)

    assert response.status_code == 404
    assert client.get(f"/api/accounts/{account_id}", headers=other_headers).status_code == 200
