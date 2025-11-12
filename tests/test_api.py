import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_chat():
    response = client.post("/chat", json={"query": "Is this good for sensitive skin?"})
    assert response.status_code == 200


def test_recommend():
    response = client.post(
        "/recommend", json={"query": "moisturizer under $25", "filters": {}}
    )
    assert response.status_code == 200


def test_filters():
    response = client.get("/filters")
    assert response.status_code == 200
