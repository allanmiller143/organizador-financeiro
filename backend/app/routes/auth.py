import uuid

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.errors import AppError
from app.extensions import db, jwt
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn
from app.schemas.password_reset import (
    PasswordChangeIn,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
)
from app.services import auth_service

bp = Blueprint("auth", __name__)


def _user_json(user: User) -> dict:
    return {"id": str(user.id), "name": user.name, "email": user.email}


def _tokens(user: User) -> dict:
    identity = str(user.id)
    claims = {"auth_version": user.auth_version}
    return {
        "access_token": create_access_token(identity=identity, additional_claims=claims),
        "refresh_token": create_refresh_token(identity=identity, additional_claims=claims),
    }


@jwt.token_in_blocklist_loader
def _is_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
    try:
        user_id = uuid.UUID(jwt_payload["sub"])
    except (KeyError, TypeError, ValueError):
        return True
    user = db.session.get(User, user_id)
    if user is None:
        return True
    return int(jwt_payload.get("auth_version", 0)) != user.auth_version


@bp.post("/register")
def register():
    data = RegisterIn.model_validate(request.get_json(silent=True) or {})
    user = auth_service.register_user(data.name, data.email, data.password)
    return jsonify(user=_user_json(user), **_tokens(user)), 201


@bp.post("/login")
def login():
    data = LoginIn.model_validate(request.get_json(silent=True) or {})
    try:
        user = auth_service.authenticate(data.email, data.password)
    except AppError:
        current_app.logger.warning("Login inválido a partir de %s", request.remote_addr)
        raise
    return jsonify(user=_user_json(user), **_tokens(user))


@bp.post("/password-reset/request")
def request_password_reset():
    data = PasswordResetRequestIn.model_validate(request.get_json(silent=True) or {})
    reset_url = auth_service.request_password_reset(data.email)
    response = {
        "message": "Se o e-mail estiver cadastrado, enviaremos um link para redefinir a senha."
    }
    # Link retornado somente em desenvolvimento/testes; nunca em produção.
    if reset_url and current_app.config.get("PASSWORD_RESET_DEBUG", False):
        response["debug_reset_url"] = reset_url
    return jsonify(response)


@bp.post("/password-reset/confirm")
def confirm_password_reset():
    data = PasswordResetConfirmIn.model_validate(request.get_json(silent=True) or {})
    auth_service.reset_password(data.token, data.password)
    return jsonify(message="Senha redefinida. Entre usando a nova senha.")


@bp.post("/password/change")
@jwt_required()
def change_password():
    user = db.session.get(User, uuid.UUID(get_jwt_identity()))
    if user is None:
        raise AppError("Usuário não encontrado.", 404, "user_not_found")
    data = PasswordChangeIn.model_validate(request.get_json(silent=True) or {})
    auth_service.change_password(user, data.current_password, data.new_password)
    return jsonify(
        message="Senha alterada com segurança.",
        **_tokens(user),
    )


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    claims = {"auth_version": int(get_jwt().get("auth_version", 0))}
    return jsonify(
        access_token=create_access_token(
            identity=get_jwt_identity(), additional_claims=claims
        )
    )


@bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, uuid.UUID(get_jwt_identity()))
    if user is None:
        raise AppError("Usuário não encontrado.", 404, "user_not_found")
    return jsonify(user=_user_json(user))
