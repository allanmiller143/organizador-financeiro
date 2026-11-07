from app import create_app


def test_health_returns_ok():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}