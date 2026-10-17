"""
Project Atlas - Automated Tests for FastAPI Endpoints (Milestone 6)
Verifies:
1. GET /health status check.
2. Authentication enforcement (401 on missing key).
3. Client spoofing protection (403 on client_id mismatch).
4. POST /chat endpoint execution and full response contract.
5. POST /ingest admin authorization check.
6. GET /escalations retrieval.
7. POST /feedback message rating persistence.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

KEY_C01 = "client_key_c01_northwind_utilities_secret_2026"
KEY_C02 = "client_key_c02_blue_delta_infra_secret_2026"
ADMIN_KEY = "atlas-admin-secret-key-change-in-production"


def test_api_health_endpoint():
    """Verify GET /health returns operational status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert "api" in data["components"]
    assert data["components"]["api"]["status"] == "ok"


def test_api_chat_authentication_required():
    """Verify POST /chat rejects unauthenticated requests with 401."""
    payload = {
        "client_id": "C-01",
        "question": "What was the smart water meter market size in 2024?"
    }
    resp = client.post("/chat", json=payload)
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


def test_api_chat_client_spoofing_rejected():
    """Verify POST /chat rejects requests where API key belongs to C-01 but client_id is C-02."""
    payload = {
        "client_id": "C-02",
        "question": "What was the smart water meter market size in 2024?"
    }
    headers = {"X-Client-Key": KEY_C01}
    resp = client.post("/chat", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "cannot execute queries for C-02" in resp.json()["detail"]


def test_api_chat_successful_factual_flow():
    """Verify POST /chat returns full response contract for authorized client."""
    payload = {
        "client_id": "C-01",
        "question": "What was the smart water meter market size in 2024?"
    }
    headers = {"X-Client-Key": KEY_C01}
    resp = client.post("/chat", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Validate all required fields in API contract
    assert "answer" in data and len(data["answer"]) > 0
    assert "citations" in data
    assert "confidence" in data and 0.0 <= data["confidence"] <= 1.0
    assert "conflicts" in data
    assert "derived_values" in data
    assert "escalated" in data and isinstance(data["escalated"], bool)
    assert "request_id" in data
    assert "latency_ms" in data


def test_api_ingest_admin_protection():
    """Verify POST /ingest enforces administrative authorization."""
    # 1. Unauthenticated or non-admin rejected
    resp_unauth = client.post("/ingest", json={})
    assert resp_unauth.status_code == 403

    # 2. Valid admin key authorized
    headers = {"X-Admin-Key": ADMIN_KEY}
    resp_admin = client.post("/ingest", json={"reports_directory": "reports"}, headers=headers)
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert data["success"] is True
    assert data["reports_ingested"] >= 6


def test_api_escalations_endpoint():
    """Verify GET /escalations returns tickets for authenticated client."""
    headers = {"X-Client-Key": KEY_C01}
    resp = client.get("/escalations", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_api_feedback_endpoint():
    """Verify POST /feedback records thumbs-up rating."""
    payload = {
        "message_id": "msg-test-12345",
        "client_id": "C-01",
        "rating": "thumbs_up",
        "comment": "Accurate figures and well cited."
    }
    headers = {"X-Client-Key": KEY_C01}
    resp = client.post("/feedback", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
