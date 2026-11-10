import os

from flask import Flask
from flask_cors import CORS

from app.config import config_by_name
from app.errors import register_error_handlers, register_jwt_error_handlers
from app.extensions import db, jwt, migrate
from app.logging_config import configure_logging


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    allowed_origins = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    CORS(
        app,
        resources={r"/api/*": {"origins": [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]}},
    )

    configure_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app import models  # noqa: F401  (registra os modelos)
    from app.cli import register_cli
    from app.routes import register_routes

    register_routes(app)
    register_error_handlers(app)
    register_jwt_error_handlers(jwt)
    register_cli(app)

    return app
