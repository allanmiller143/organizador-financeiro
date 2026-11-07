from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.schemas.cdi import CdiQuery, CdiRateOut
from app.services import cdi_service

bp = Blueprint("cdi", __name__)


@bp.get("")
@jwt_required()
def list_rates():
    query = CdiQuery.model_validate(request.args.to_dict())
    rates = cdi_service.list_rates(**query.model_dump())
    return jsonify(
        rates=[CdiRateOut.model_validate(r).model_dump(mode="json") for r in rates]
    )