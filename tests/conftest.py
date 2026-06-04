"""
Shared fixtures for all ClaimPilot test suites.

- client / auth_headers  : mocked DB + graph (no external deps — fast)
- live_client / live_token: real DB + real Groq LLM (requires running stack)
"""
import sys
import os
import uuid
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Mock graph helpers ───────────────────────────────────────────────────────

def _make_mock_graph(case_state=None):
    graph = MagicMock()
    snapshot = MagicMock()
    snapshot.values = case_state or {}
    graph.get_state.return_value = snapshot
    graph.invoke.return_value = {
        "last_response": "Hello! I am ClaimPilot, your personal insurance assistant.",
        "pending_docs": [],
        "collected_docs": [],
        "case_status": "active",
        "intent": "",
    }
    return graph


# ─── Mock-based fixtures (no DB, no LLM) ─────────────────────────────────────

@pytest.fixture
def mock_graph():
    """Patch get_graph in all route modules and return the mock."""
    g = _make_mock_graph()
    with patch("routes.chat.get_graph", return_value=g), \
         patch("routes.upload.get_graph", return_value=g), \
         patch("routes.cases.get_graph", return_value=g):
        yield g


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture
def client(mock_db):
    from main import app
    from db.postgres import get_db
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def valid_token():
    from core.security import create_token
    return create_token(str(uuid.uuid4()))


@pytest.fixture
def auth_headers(valid_token):
    return {"Authorization": f"Bearer {valid_token}"}


# ─── Live fixtures (real DB + real Groq LLM) ─────────────────────────────────

@pytest.fixture(scope="module")
def live_client():
    from main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def live_token(live_client):
    email = f"e2e_{uuid.uuid4().hex[:8]}@claimpilot.test"
    resp = live_client.post("/auth/register", json={
        "name": "E2E Tester",
        "email": email,
        "password": "E2EPass123!",
    })
    assert resp.status_code == 200, f"Registration failed: {resp.text}"
    return f"Bearer {resp.json()['token']}"
