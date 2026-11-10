from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    """Erro previsto do sistema, com status HTTP e mensagem para o cliente."""

    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _error(code: str, message: str, status: int, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return _error(err.code, err.message, err.status_code)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]}
            for e in err.errors()
        ]
        return _error("validation_error", "Dados inválidos.", 422, details)

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        code = err.name.lower().replace(" ", "_")
        return _error(code, err.description, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception("Erro inesperado")
        return _error("internal_error", "Erro interno do servidor.", 500)


def register_jwt_error_handlers(jwt: JWTManager) -> None:
    @jwt.unauthorized_loader
    def missing_token(reason):
        return _error("missing_token", "Token de acesso ausente.", 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return _error("invalid_token", "Token inválido.", 401)

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return _error("token_expired", "Token expirado.", 401)

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return _error("token_revoked", "Sessão encerrada. Entre novamente.", 401)
