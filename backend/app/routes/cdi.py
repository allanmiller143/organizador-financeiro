from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.schemas.cdi import CdiQuery, CdiRateOut
from app.services import cdi_service

bp = Blueprint("cdi", __name__)


@bp.post("/sync")
@jwt_required()
def sync_rates():
    inserted, latest_date = cdi_service.sync_cdi_now()
    return jsonify(
        inserted=inserted,
        latest_date=latest_date.isoformat() if latest_date else None,
        message=(
            f"{inserted} dia(s) novo(s) de CDI atualizado(s)."
            if inserted
            else "Não há novos dados publicados pelo Banco Central no momento."
        ),
    )


@bp.get("")
@jwt_required()
def list_rates():
    query = CdiQuery.model_validate(request.args.to_dict())
    rates = cdi_service.list_rates(**query.model_dump())
    return jsonify(
        rates=[CdiRateOut.model_validate(r).model_dump(mode="json") for r in rates]
    )
