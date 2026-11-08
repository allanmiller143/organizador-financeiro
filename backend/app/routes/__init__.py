from flask import Flask

from app.routes.accounts import bp as accounts_bp
from app.routes.auth import bp as auth_bp
from app.routes.cdi import bp as cdi_bp
from app.routes.health import bp as health_bp
from app.routes.projections import bp as projections_bp
from app.routes.reports import bp as reports_bp
from app.routes.transactions import bp as transactions_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    app.register_blueprint(transactions_bp, url_prefix="/api")
    app.register_blueprint(cdi_bp, url_prefix="/api/cdi")
    app.register_blueprint(reports_bp, url_prefix="/api")
    app.register_blueprint(projections_bp, url_prefix="/api/projections")