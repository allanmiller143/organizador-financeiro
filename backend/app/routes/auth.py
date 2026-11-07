import uuid

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from app.errors import AppError
from app.extensions import db
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn
from app.services import auth_service

bp = Blueprint("auth", __name__)


def _user_json(user: User) -> dict:
    return {"id": str(user.id), "name": user.name, "email": user.email}


def _tokens(user: User) -> dict:
    identity = str(user.id)
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
    }


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


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return jsonify(access_token=create_access_token(identity=get_jwt_identity()))


@bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, uuid.UUID(get_jwt_identity()))
    if user is None:
        raise AppError("Usuário não encontrado.", 404, "user_not_found")
    return jsonify(user=_user_json(user))