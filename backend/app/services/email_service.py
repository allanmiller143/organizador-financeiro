from html import escape

import requests
from flask import current_app

BREVO_EMAILS_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


class EmailDeliveryError(Exception):
    """Provider unavailable or rejected the transactional message."""


def password_reset_email_is_configured() -> bool:
    return bool(
        current_app.config.get("BREVO_API_KEY")
        and current_app.config.get("BREVO_FROM_EMAIL")
    )


def send_password_reset_email(to_email: str, reset_url: str) -> str:
    api_key = current_app.config["BREVO_API_KEY"]
    sender_email = current_app.config["BREVO_FROM_EMAIL"]
    sender_name = current_app.config.get("BREVO_FROM_NAME", "Organizador Financeiro")
    safe_url = escape(reset_url, quote=True)
    subject = "Redefina sua senha — Organizador Financeiro"
    text = (
        "Recebemos um pedido para redefinir a senha da sua conta.\n\n"
        f"Use este link em até 30 minutos:\n{reset_url}\n\n"
        "Se você não pediu a redefinição, ignore esta mensagem."
    )
    html = f"""<!doctype html>
<html lang="pt-BR">
  <body style="margin:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#0f172a">
    <main style="max-width:560px;margin:32px auto;padding:32px;background:#ffffff;border-radius:16px">
      <p style="margin:0 0 8px;color:#0f766e;font-size:13px;font-weight:700">ORGANIZADOR FINANCEIRO</p>
      <h1 style="margin:0 0 16px;font-size:24px">Redefina sua senha</h1>
      <p style="line-height:1.6">Recebemos um pedido para criar uma nova senha para sua conta.</p>
      <p style="margin:24px 0">
        <a href="{safe_url}" style="display:inline-block;padding:12px 20px;border-radius:10px;background:#0f766e;color:#ffffff;text-decoration:none;font-weight:700">Criar nova senha</a>
      </p>
      <p style="line-height:1.6">O link expira em 30 minutos e só pode ser usado uma vez. Se você não pediu a redefinição, ignore este e-mail.</p>
      <p style="margin-top:24px;color:#64748b;font-size:12px;line-height:1.6">Se o botão não funcionar, copie este endereço para o navegador:<br><a href="{safe_url}" style="color:#0f766e;word-break:break-all">{safe_url}</a></p>
    </main>
  </body>
</html>"""
    headers = {
        "api-key": api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": text,
        "htmlContent": html,
    }

    try:
        response = requests.post(
            BREVO_EMAILS_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=(5, 15),
        )
    except requests.RequestException as exc:
        current_app.logger.warning("API da Brevo não pôde ser acessada (%s)", type(exc).__name__)
        raise EmailDeliveryError("Email provider request failed") from exc

    if not response.ok:
        current_app.logger.warning("API da Brevo recusou o envio (HTTP %s)", response.status_code)
        raise EmailDeliveryError("Email provider rejected the message")

    try:
        message_id = response.json().get("messageId")
    except (ValueError, AttributeError):
        message_id = None
    if message_id:
        current_app.logger.info("Brevo aceitou o e-mail transacional (messageId=%s)", message_id)
    return str(message_id or "accepted")
