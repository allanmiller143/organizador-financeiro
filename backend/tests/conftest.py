import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register(client, email):
    response = client.post(
        "/api/auth/register",
        json={"name": "Teste", "email": email, "password": "senha-forte-123"},
    )
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


@pytest.fixture()
def auth_headers(client):
    return _register(client, "allan@example.com")


@pytest.fixture()
def other_headers(client):
    return _register(client, "outra@example.com")