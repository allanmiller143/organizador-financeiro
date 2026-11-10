from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from urllib.parse import quote

from flask import current_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.errors import AppError
from app.extensions import db
from app.models import User
from app.security import hash_password, verify_password
from app.services.email_service import (
    password_reset_email_is_configured,
    send_password_reset_email,
)


def register_user(name: str, email: str, password: str) -> User:
    if db.session.scalar(select(User).where(User.email == email)):
        raise AppError("E-mail já cadastrado.", 409, "email_taken")

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # duas requisições ao mesmo tempo com o mesmo e-mail
        db.session.rollback()
        raise AppError("E-mail já cadastrado.", 409, "email_taken")
    return user


def authenticate(email: str, password: str) -> User:
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(user.password_hash, password):
        raise AppError("E-mail ou senha incorretos.", 401, "invalid_credentials")
    return user


def request_password_reset(email: str) -> str | None:
    debug_mode = bool(current_app.config.get("PASSWORD_RESET_DEBUG", False))
    if not debug_mode and not password_reset_email_is_configured():
        raise AppError(
            "O envio de e-mail para redefinir a senha ainda não está configurado.",
            503,
            "password_reset_unavailable",
        )

    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    ttl_minutes = int(current_app.config.get("PASSWORD_RESET_TOKEN_MINUTES", 30))
    user.password_reset_token_hash = token_hash
    user.password_reset_expires_at = now + timedelta(minutes=ttl_minutes)
    db.session.commit()

    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_url = f"{frontend_url}/#/redefinir-senha?token={quote(raw_token)}"
    if debug_mode:
        return reset_url

    try:
        send_password_reset_email(user.email, reset_url)
    except Exception as exc:
        current_app.logger.exception("Falha ao enviar e-mail de redefinição")
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        db.session.commit()
        raise AppError(
            "Não foi possível enviar o e-mail agora. Tente novamente mais tarde.",
            503,
            "password_reset_email_failed",
        ) from exc
    return None


def reset_password(token: str, password: str) -> None:
    token_hash = sha256(token.encode("utf-8")).hexdigest()
    user = db.session.scalar(
        select(User).where(User.password_reset_token_hash == token_hash)
    )
    if user is None or user.password_reset_expires_at is None:
        raise AppError("Link de redefinição inválido ou expirado.", 400, "invalid_reset_token")

    expires_at = user.password_reset_expires_at
    if expires_at.tzinfo is None:  # SQLite devolve DateTime sem timezone.
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        db.session.commit()
        raise AppError("Link de redefinição inválido ou expirado.", 400, "invalid_reset_token")

    user.password_hash = hash_password(password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.auth_version += 1
    db.session.commit()
