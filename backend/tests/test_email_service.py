from unittest.mock import Mock, patch

import pytest
import requests

from app.services.email_service import (
    BREVO_EMAILS_ENDPOINT,
    EmailDeliveryError,
    send_password_reset_email,
)


def test_brevo_email_uses_https_api_key_and_html_text_alternatives(app):
    app.config.update(
        BREVO_API_KEY="xkeysib_test_secret",
        BREVO_FROM_EMAIL="sender@example.com",
        BREVO_FROM_NAME="Organizador Financeiro",
    )
    response = Mock(ok=True, status_code=201, headers={})
    response.json.return_value = {"messageId": "<email-test-id>"}

    with app.app_context(), patch(
        "app.services.email_service.requests.post", return_value=response
    ) as post:
        message_id = send_password_reset_email(
            "recipient@example.com", "https://app.example.com/#/redefinir-senha?token=abc"
        )

    assert message_id == "<email-test-id>"
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == BREVO_EMAILS_ENDPOINT
    assert kwargs["headers"]["api-key"] == "xkeysib_test_secret"
    assert kwargs["timeout"] == (5, 15)
    payload = kwargs["json"]
    assert payload["sender"] == {
        "name": "Organizador Financeiro",
        "email": "sender@example.com",
    }
    assert payload["to"] == [{"email": "recipient@example.com"}]
    assert "token=abc" in payload["textContent"]
    assert "href=\"https://app.example.com/#/redefinir-senha?token=abc\"" in payload["htmlContent"]


def test_brevo_network_failure_is_classified_and_not_exposed_as_raw_socket_error(app):
    app.config.update(
        BREVO_API_KEY="xkeysib_test_secret",
        BREVO_FROM_EMAIL="sender@example.com",
    )
    with app.app_context(), patch(
        "app.services.email_service.requests.post",
        side_effect=requests.ConnectionError("network unreachable"),
    ):
        with pytest.raises(EmailDeliveryError):
            send_password_reset_email(
                "recipient@example.com", "https://app.example.com/#/redefinir-senha?token=abc"
            )


def test_brevo_rejection_raises_safe_delivery_error(app):
    app.config.update(
        BREVO_API_KEY="xkeysib_test_secret",
        BREVO_FROM_EMAIL="sender@example.com",
    )
    response = Mock(ok=False, status_code=401, headers={})

    with app.app_context(), patch(
        "app.services.email_service.requests.post", return_value=response
    ):
        with pytest.raises(EmailDeliveryError):
            send_password_reset_email(
                "recipient@example.com", "https://app.example.com/#/redefinir-senha?token=abc"
            )
