from app.extensions import db
from app.models import User

USER = {"name": "Allan", "email": "allan@example.com", "password": "senha-forte-123"}


def register(client):
    return client.post("/api/auth/register", json=USER)


def test_register_creates_user_without_exposing_password(client):
    response = register(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "allan@example.com"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]
    assert body["access_token"] and body["refresh_token"]


def test_password_is_stored_hashed(client):
    register(client)

    user = db.session.query(User).one()
    assert user.password_hash != USER["password"]
    assert user.password_hash.startswith("$argon2")


def test_register_duplicate_email_returns_409(client):
    register(client)

    response = register(client)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "email_taken"


def test_register_invalid_data_returns_422(client):
    response = client.post(
        "/api/auth/register", json={"name": "A", "email": "nao-e-email", "password": "123"}
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"


def test_login_with_correct_password(client):
    register(client)

    response = client.post(
        "/api/auth/login", json={"email": USER["email"], "password": USER["password"]}
    )

    assert response.status_code == 200
    assert response.get_json()["access_token"]


def test_login_with_wrong_password_returns_401(client):
    register(client)

    response = client.post(
        "/api/auth/login", json={"email": USER["email"], "password": "senha-errada-1"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"


def test_me_without_token_returns_401(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "missing_token"


def test_me_with_token_returns_user(client):
    token = register(client).get_json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "allan@example.com"


def test_refresh_token_gives_new_access_token(client):
    refresh_token = register(client).get_json()["refresh_token"]

    response = client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 200
    assert response.get_json()["access_token"]


def test_access_token_cannot_be_used_to_refresh(client):
    access_token = register(client).get_json()["access_token"]

    response = client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 401