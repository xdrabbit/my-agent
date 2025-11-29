from fastapi.testclient import TestClient
from nyra_realtime.main import app

client = TestClient(app)

def test_readiness():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_health_ping():
    r = client.get("/health/ping")
    assert r.status_code == 200
    assert "app" in r.json()

def test_admin_unauthorized():
    r = client.get("/control/status")
    assert r.status_code == 401

def test_twilio_webhook():
    payload = {"call_sid": "CS1", "direction": "inbound"}
    r = client.post("/telephony/webhook", json=payload)
    assert r.status_code == 200
    assert r.json()["call_sid"] == "CS1"
