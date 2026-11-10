from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from app.extensions import db
from app.models import User

USER = {"name": "Allan", "email": "allan@example.com", "password": "senha-forte-123"}


def register(client):
    return client.post("/api/auth/register", json=USER)


def test_password_reset_request_is_generic_for_unknown_email(client):
    register(client)
    known = client.post("/api/auth/password-reset/request", json={"email": USER["email"]})
    unknown = client.post("/api/auth/password-reset/request", json={"email": "ausente@example.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.get_json()["message"] == unknown.get_json()["message"]
    assert "debug_reset_url" in known.get_json()
    assert "debug_reset_url" not in unknown.get_json()


def test_password_reset_changes_password_and_revokes_old_tokens(client):
    original = register(client).get_json()
    requested = client.post(
        "/api/auth/password-reset/request", json={"email": USER["email"]}
    ).get_json()
    token = parse_qs(urlparse(requested["debug_reset_url"]).fragment.split("?", 1)[1])["token"][0]

    response = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "password": "senha-nova-forte-456"},
    )

    assert response.status_code == 200
    assert client.post(
        "/api/auth/login", json={"email": USER["email"], "password": USER["password"]}
    ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"email": USER["email"], "password": "senha-nova-forte-456"},
    ).status_code == 200
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {original['access_token']}"}
    ).status_code == 401
    assert client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {original['refresh_token']}"}
    ).status_code == 401


def test_password_reset_token_is_single_use(client):
    register(client)
    requested = client.post(
        "/api/auth/password-reset/request", json={"email": USER["email"]}
    ).get_json()
    token = parse_qs(urlparse(requested["debug_reset_url"]).fragment.split("?", 1)[1])["token"][0]
    body = {"token": token, "password": "senha-nova-forte-456"}

    assert client.post("/api/auth/password-reset/confirm", json=body).status_code == 200
    response = client.post("/api/auth/password-reset/confirm", json=body)

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_reset_token"


def test_password_reset_request_sends_email_when_debug_mode_is_disabled(client, app):
    register(client)
    app.config.update(
        PASSWORD_RESET_DEBUG=False,
        MAIL_SERVER="smtp.example.com",
        MAIL_PORT=587,
        MAIL_USERNAME="sender@example.com",
        MAIL_PASSWORD="smtp-secret",
        MAIL_DEFAULT_SENDER="sender@example.com",
        FRONTEND_URL="https://app.example.com",
    )

    with patch("app.services.auth_service.send_password_reset_email") as send_email:
        response = client.post(
            "/api/auth/password-reset/request", json={"email": USER["email"]}
        )

    assert response.status_code == 200
    assert "debug_reset_url" not in response.get_json()
    send_email.assert_called_once()
    reset_url = send_email.call_args.args[1]
    assert reset_url.startswith("https://app.example.com/#/redefinir-senha?token=")


def test_production_requires_mail_configuration_without_revealing_account(client, app):
    register(client)
    app.config.update(PASSWORD_RESET_DEBUG=False, MAIL_SERVER=None)

    known = client.post("/api/auth/password-reset/request", json={"email": USER["email"]})
    unknown = client.post(
        "/api/auth/password-reset/request", json={"email": "ausente@example.com"}
    )

    assert known.status_code == unknown.status_code == 503
    assert known.get_json() == unknown.get_json()
    assert db.session.query(User).one().password_reset_token_hash is None
