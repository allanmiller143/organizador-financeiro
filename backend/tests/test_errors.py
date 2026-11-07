from app import create_app
from app.errors import AppError


def make_client():
    app = create_app("testing")

    @app.get("/api/_boom")
    def boom():
        raise AppError("Valor inválido", 422, "validation_error")

    @app.get("/api/_crash")
    def crash():
        raise RuntimeError("segredo interno")

    return app.test_client()


def test_not_found_returns_json():
    response = make_client().get("/api/nao-existe")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_app_error_returns_json():
    response = make_client().get("/api/_boom")

    assert response.status_code == 422
    assert response.get_json() == {
        "error": {"code": "validation_error", "message": "Valor inválido"}
    }


def test_unexpected_error_hides_details():
    response = make_client().get("/api/_crash")

    assert response.status_code == 500
    assert "segredo interno" not in response.get_data(as_text=True)