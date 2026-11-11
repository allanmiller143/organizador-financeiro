from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from app.extensions import db
from app.models import User
from app.services.email_service import EmailDeliveryError

USER = {"name": "Allan", "email": "allan@example.com", "password": "senha-forte-123"}


def register(client):
    return client.post("/api/auth/register", json=USER)


def token_from_debug_url(url: str) -> str:
    query = urlparse(url).fragment.split("?", 1)[1]
    return parse_qs(query)["token"][0]


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
    token = token_from_debug_url(requested["debug_reset_url"])

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
    token = token_from_debug_url(requested["debug_reset_url"])
    body = {"token": token, "password": "senha-nova-forte-456"}

    assert client.post("/api/auth/password-reset/confirm", json=body).status_code == 200
    response = client.post("/api/auth/password-reset/confirm", json=body)

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_reset_token"


def test_password_reset_request_sends_email_when_debug_mode_is_disabled(client, app):
    register(client)
    app.config.update(
        PASSWORD_RESET_DEBUG=False,
        BREVO_API_KEY="xkeysib-test-key",
        BREVO_FROM_EMAIL="sender@example.com",
        BREVO_FROM_NAME="Organizador Financeiro",
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


def test_provider_failure_returns_json_error_and_preserves_token_for_ambiguous_delivery(client, app):
    register(client)
    app.config.update(
        PASSWORD_RESET_DEBUG=False,
        BREVO_API_KEY="xkeysib-test-key",
        BREVO_FROM_EMAIL="sender@example.com",
    )
    with patch(
        "app.services.auth_service.send_password_reset_email",
        side_effect=EmailDeliveryError("temporary provider failure"),
    ):
        response = client.post(
            "/api/auth/password-reset/request", json={"email": USER["email"]}
        )

    assert response.status_code == 503
    assert response.is_json
    assert response.get_json()["error"]["code"] == "password_reset_email_failed"
    assert db.session.query(User).one().password_reset_token_hash is not None


def test_production_requires_provider_configuration_without_revealing_account(client, app):
    register(client)
    app.config.update(
        PASSWORD_RESET_DEBUG=False,
        BREVO_API_KEY=None,
        BREVO_FROM_EMAIL=None,
    )

    known = client.post("/api/auth/password-reset/request", json={"email": USER["email"]})
    unknown = client.post(
        "/api/auth/password-reset/request", json={"email": "ausente@example.com"}
    )

    assert known.status_code == unknown.status_code == 503
    assert known.get_json() == unknown.get_json()
    assert db.session.query(User).one().password_reset_token_hash is None


def test_authenticated_password_change_rotates_tokens_and_keeps_current_session(client):
    session = register(client).get_json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = client.post(
        "/api/auth/password/change",
        headers=headers,
        json={"current_password": USER["password"], "new_password": "senha-perfil-nova-789"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access_token"] and payload["refresh_token"]
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"}
    ).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {session['refresh_token']}"},
    ).status_code == 401
    assert client.post(
        "/api/auth/login", json={"email": USER["email"], "password": "senha-perfil-nova-789"}
    ).status_code == 200


def test_password_change_rejects_wrong_current_password_without_revoking_session(client):
    session = register(client).get_json()
    response = client.post(
        "/api/auth/password/change",
        headers={"Authorization": f"Bearer {session['access_token']}"},
        json={"current_password": "errada", "new_password": "senha-perfil-nova-789"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "current_password_invalid"
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {session['access_token']}"}
    ).status_code == 200
