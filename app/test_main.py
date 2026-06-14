from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_dodaj():
    response = client.post("/dodaj", json={"a": 10, "b": 5})
    assert response.json()["wynik"] == 15

def test_odejmij():
    response = client.post("/odejmij", json={"a": 10, "b": 3})
    assert response.json()["wynik"] == 7

def test_mnoz():
    response = client.post("/mnoz", json={"a": 4, "b": 3})
    assert response.json()["wynik"] == 12

def test_dziel():
    response = client.post("/dziel", json={"a": 10, "b": 2})
    assert response.json()["wynik"] == 5.0

def test_dziel_przez_zero():
    response = client.post("/dziel", json={"a": 10, "b": 0})
    assert response.status_code == 400