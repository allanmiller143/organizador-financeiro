from flask import Flask

from app.routes.auth import bp as auth_bp
from app.routes.health import bp as health_bp
from app.routes.accounts import bp as accounts_bp

def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")