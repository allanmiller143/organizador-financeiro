import uuid

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.schemas.report import DashboardOut, MonthlyYieldsOut, SummaryOut
from app.services import report_service

bp = Blueprint("reports", __name__)


def _user_id() -> uuid.UUID:
    return uuid.UUID(get_jwt_identity())


@bp.get("/accounts/<uuid:account_id>/summary")
@jwt_required()
def account_summary(account_id):
    data = report_service.account_summary(_user_id(), account_id)
    return jsonify(summary=SummaryOut(**data).model_dump(mode="json"))


@bp.get("/accounts/<uuid:account_id>/monthly-yields")
@jwt_required()
def account_monthly_yields(account_id):
    data = report_service.account_monthly_yields(_user_id(), account_id)
    return jsonify(monthly_yields=MonthlyYieldsOut(**data).model_dump(mode="json"))


@bp.get("/dashboard")
@jwt_required()
def dashboard():
    data = report_service.dashboard(_user_id())
    return jsonify(dashboard=DashboardOut(**data).model_dump(mode="json"))