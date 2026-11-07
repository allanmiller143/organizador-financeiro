from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    """Erro previsto do sistema, com status HTTP e mensagem para o cliente."""

    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        body = {"error": {"code": err.code, "message": err.message}}
        return jsonify(body), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        code = err.name.lower().replace(" ", "_")
        body = {"error": {"code": code, "message": err.description}}
        return jsonify(body), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception("Erro inesperado")
        body = {"error": {"code": "internal_error", "message": "Erro interno do servidor."}}
        return jsonify(body), 500