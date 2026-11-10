import smtplib
from email.message import EmailMessage

from flask import current_app


def password_reset_email_is_configured() -> bool:
    return all(
        current_app.config.get(name)
        for name in (
            "MAIL_SERVER",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            "MAIL_DEFAULT_SENDER",
        )
    )


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Redefinição de senha — Organizador Financeiro"
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = to_email
    message.set_content(
        "Recebemos um pedido para redefinir a senha da sua conta.\n\n"
        f"Use este link em até 30 minutos:\n{reset_url}\n\n"
        "Se você não pediu a redefinição, ignore esta mensagem."
    )

    host = current_app.config["MAIL_SERVER"]
    port = current_app.config.get("MAIL_PORT", 587)
    timeout = current_app.config.get("MAIL_TIMEOUT", 15)
    username = current_app.config["MAIL_USERNAME"]
    password = current_app.config["MAIL_PASSWORD"]

    with smtplib.SMTP(host, port, timeout=timeout) as smtp:
        smtp.ehlo()
        if current_app.config.get("MAIL_USE_TLS", True):
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)
