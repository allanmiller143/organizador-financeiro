from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.schemas.projection import SimulationIn, SimulationOut
from app.services import projection_service

bp = Blueprint("projections", __name__)


@bp.post("/simulate")
@jwt_required()
def simulate():
    data = SimulationIn.model_validate(request.get_json(silent=True) or {})
    result = projection_service.simulate(data.model_dump())
    return jsonify(simulation=SimulationOut(**result).model_dump(mode="json"))