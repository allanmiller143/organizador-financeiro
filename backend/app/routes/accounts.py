import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Account
from app.schemas.account import AccountIn, AccountOut, AccountUpdate
from app.services import account_service, report_service

bp = Blueprint("accounts", __name__)


def _user_id() -> uuid.UUID:
    return uuid.UUID(get_jwt_identity())


def _json(account: Account) -> dict:
    return AccountOut.model_validate(account).model_dump(mode="json")


@bp.get("")
@jwt_required()
def list_accounts():
    accounts = account_service.list_accounts(_user_id())
    return jsonify(accounts=[_json(a) for a in accounts])


@bp.post("")
@jwt_required()
def create_account():
    data = AccountIn.model_validate(request.get_json(silent=True) or {})
    account = account_service.create_account(_user_id(), data.model_dump())
    return jsonify(account=_json(account)), 201


@bp.get("/<uuid:account_id>")
@jwt_required()
def get_account(account_id):
    return jsonify(account=_json(account_service.get_account(_user_id(), account_id)))


@bp.patch("/<uuid:account_id>")
@jwt_required()
def update_account(account_id):
    data = AccountUpdate.model_validate(request.get_json(silent=True) or {})
    changes = data.model_dump(exclude_unset=True)
    account = account_service.update_account(_user_id(), account_id, changes)
    return jsonify(account=_json(account))


@bp.get("/<uuid:account_id>/goal-forecast")
@jwt_required()
def goal_forecast(account_id):
    return jsonify(forecast=report_service.account_goal_forecast(_user_id(), account_id))


@bp.delete("/<uuid:account_id>")
@jwt_required()
def delete_account(account_id):
    account_service.delete_account(_user_id(), account_id)
    return "", 204
