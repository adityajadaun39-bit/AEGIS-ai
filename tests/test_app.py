from fastapi.testclient import TestClient

from backend import config
from backend.app import app

client = TestClient(app)


def test_root_returns_project_info():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "ok",
    }


def test_health_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
