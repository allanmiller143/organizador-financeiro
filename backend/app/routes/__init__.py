from flask import Flask

from app.routes.health import bp as health_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api")