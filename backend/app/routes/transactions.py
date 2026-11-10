import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Transaction
from app.schemas.transaction import (
    TransactionFilters,
    TransactionIn,
    TransactionOrderIn,
    TransactionOut,
    TransactionUpdate,
)
from app.services import transaction_service

bp = Blueprint("transactions", __name__)


def _user_id() -> uuid.UUID:
    return uuid.UUID(get_jwt_identity())


def _json(transaction: Transaction) -> dict:
    return TransactionOut.model_validate(transaction).model_dump(mode="json")


@bp.get("/accounts/<uuid:account_id>/transactions")
@jwt_required()
def list_transactions(account_id):
    filters = TransactionFilters.model_validate(request.args.to_dict())
    transactions = transaction_service.list_transactions(
        _user_id(), account_id, **filters.model_dump()
    )
    return jsonify(transactions=[_json(t) for t in transactions])


@bp.post("/accounts/<uuid:account_id>/transactions")
@jwt_required()
def create_transaction(account_id):
    data = TransactionIn.model_validate(request.get_json(silent=True) or {})
    transaction = transaction_service.create_transaction(
        _user_id(), account_id, data.model_dump()
    )
    return jsonify(transaction=_json(transaction)), 201


@bp.patch("/transactions/<uuid:transaction_id>")
@jwt_required()
def update_transaction(transaction_id):
    data = TransactionUpdate.model_validate(request.get_json(silent=True) or {})
    changes = data.model_dump(exclude_unset=True)
    transaction = transaction_service.update_transaction(
        _user_id(), transaction_id, changes
    )
    return jsonify(transaction=_json(transaction))


@bp.patch("/accounts/<uuid:account_id>/transactions/order")
@jwt_required()
def reorder_transactions(account_id):
    data = TransactionOrderIn.model_validate(request.get_json(silent=True) or {})
    transaction_service.reorder_transactions(
        _user_id(), account_id, data.transaction_ids
    )
    return "", 204


@bp.patch("/accounts/<uuid:account_id>/reapplications/order")
@jwt_required()
def reorder_reapplications(account_id):
    data = TransactionOrderIn.model_validate(request.get_json(silent=True) or {})
    transaction_service.reorder_reapplications(
        _user_id(), account_id, data.transaction_ids
    )
    return "", 204


@bp.delete("/transactions/<uuid:transaction_id>")
@jwt_required()
def delete_transaction(transaction_id):
    transaction_service.delete_transaction(_user_id(), transaction_id)
    return "", 204
