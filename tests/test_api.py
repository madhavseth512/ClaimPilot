"""
API Test Suite — auth matrix + input validation matrix.

Based on api-test-suite-builder methodology (alirezarezvani/claude-skills).
All tests use mocked DB and graph — no PostgreSQL or Groq API required.

Run:  pytest tests/test_api.py -v
"""
import io
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH MATRIX
# Every authenticated endpoint must return 401 without / with a bad token.
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthMatrix:

    # ── /chat/ ────────────────────────────────────────────────────────────────

    def test_chat_no_auth_header_returns_401(self, client, mock_graph):
        with patch("guardrails.runner.check_input", new=AsyncMock(return_value=(True, ""))), \
             patch("guardrails.runner.check_output", new=AsyncMock(side_effect=lambda r: (True, r))):
            resp = client.post("/chat/", json={"message": "Hello"})
        assert resp.status_code == 401

    def test_chat_invalid_token_returns_401(self, client, mock_graph):
        with patch("guardrails.runner.check_input", new=AsyncMock(return_value=(True, ""))), \
             patch("guardrails.runner.check_output", new=AsyncMock(side_effect=lambda r: (True, r))):
            resp = client.post(
                "/chat/",
                json={"message": "Hello"},
                headers={"Authorization": "Bearer not_a_real_token"},
            )
        assert resp.status_code == 401

    def test_chat_malformed_bearer_returns_401(self, client, mock_graph):
        with patch("guardrails.runner.check_input", new=AsyncMock(return_value=(True, ""))), \
             patch("guardrails.runner.check_output", new=AsyncMock(side_effect=lambda r: (True, r))):
            resp = client.post(
                "/chat/",
                json={"message": "Hello"},
                headers={"Authorization": "Basic dXNlcjpwYXNz"},
            )
        assert resp.status_code == 401

    def test_chat_valid_token_passes_auth(self, client, mock_graph, auth_headers):
        with patch("guardrails.runner.check_input", new=AsyncMock(return_value=(True, ""))), \
             patch("guardrails.runner.check_output", new=AsyncMock(side_effect=lambda r: (True, r))):
            resp = client.post("/chat/", json={"message": "Hello"}, headers=auth_headers)
        assert resp.status_code not in (401, 403)

    # ── /cases/ ───────────────────────────────────────────────────────────────

    def test_cases_list_no_auth_returns_401(self, client):
        resp = client.get("/cases/")
        assert resp.status_code == 401

    def test_cases_list_invalid_token_returns_401(self, client):
        resp = client.get("/cases/", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401

    def test_cases_single_no_auth_returns_401(self, client):
        resp = client.get(f"/cases/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_cases_valid_token_passes_auth(self, client, mock_graph, auth_headers):
        resp = client.get("/cases/", headers=auth_headers)
        assert resp.status_code not in (401, 403)

    # ── /upload/ ──────────────────────────────────────────────────────────────

    def test_upload_no_auth_returns_401(self, client):
        resp = client.post(
            "/upload/",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"case_id": "x", "document_type": "FIR Copy"},
        )
        assert resp.status_code == 401

    def test_upload_invalid_token_returns_401(self, client):
        resp = client.post(
            "/upload/",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"case_id": "x", "document_type": "FIR Copy"},
            headers={"Authorization": "Bearer bad"},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS — register / login
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthEndpoints:

    def test_register_missing_name_returns_422(self, client):
        resp = client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
        assert resp.status_code == 422

    def test_register_missing_email_returns_422(self, client):
        resp = client.post("/auth/register", json={"name": "X", "password": "pass"})
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self, client):
        resp = client.post("/auth/register", json={"name": "X", "email": "a@b.com"})
        assert resp.status_code == 422

    def test_register_empty_body_returns_422(self, client):
        resp = client.post("/auth/register", json={})
        assert resp.status_code == 422

    def test_register_duplicate_email_returns_409(self, client, mock_db):
        existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        resp = client.post("/auth/register", json={
            "name": "X", "email": "taken@b.com", "password": "pass",
        })
        assert resp.status_code == 409

    def test_login_missing_email_returns_422(self, client):
        resp = client.post("/auth/login", json={"password": "pass"})
        assert resp.status_code == 422

    def test_login_missing_password_returns_422(self, client):
        resp = client.post("/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 422

    def test_login_wrong_credentials_returns_401(self, client):
        resp = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_register_returns_token_and_user_id(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        resp = client.post("/auth/register", json={
            "name": "Alice", "email": "alice@test.com", "password": "Secret123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert "user_id" in data
        assert len(data["token"]) > 10

    def test_login_success_returns_token(self, client, mock_db):
        from core.security import hash_password
        fake_user = MagicMock()
        fake_user.user_id = str(uuid.uuid4())
        fake_user.password_hash = hash_password("correct_password")
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user
        resp = client.post("/auth/login", json={"email": "a@b.com", "password": "correct_password"})
        assert resp.status_code == 200
        assert "token" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestChatInputValidation:

    def _chat(self, client, auth_headers, mock_graph, message):
        with patch("guardrails.runner.check_input", new=AsyncMock(return_value=(True, ""))), \
             patch("guardrails.runner.check_output", new=AsyncMock(side_effect=lambda r: (True, r))):
            return client.post("/chat/", json={"message": message}, headers=auth_headers)

    def test_missing_message_field_returns_422(self, client, auth_headers, mock_graph):
        with patch("guardrails.runner.check_input", new=AsyncMock(return_value=(True, ""))):
            resp = client.post("/chat/", json={}, headers=auth_headers)
        assert resp.status_code == 422

    def test_xss_payload_does_not_crash(self, client, auth_headers, mock_graph):
        resp = self._chat(client, auth_headers, mock_graph, "<script>alert('xss')</script>")
        assert resp.status_code != 500

    def test_xss_payload_not_reflected_raw(self, client, auth_headers, mock_graph):
        resp = self._chat(client, auth_headers, mock_graph, "<script>alert('xss')</script>")
        if resp.status_code == 200:
            assert "<script>" not in resp.json().get("response", "")

    def test_sql_injection_does_not_crash(self, client, auth_headers, mock_graph):
        resp = self._chat(client, auth_headers, mock_graph, "'; DROP TABLE users; --")
        assert resp.status_code != 500

    def test_very_long_message_does_not_crash(self, client, auth_headers, mock_graph):
        resp = self._chat(client, auth_headers, mock_graph, "A" * 10_000)
        assert resp.status_code != 500

    def test_unicode_message_does_not_crash(self, client, auth_headers, mock_graph):
        resp = self._chat(client, auth_headers, mock_graph, "मेरी गाड़ी का एक्सीडेंट हुआ 🚗")
        assert resp.status_code != 500

    def test_response_shape_has_required_fields(self, client, auth_headers, mock_graph):
        resp = self._chat(client, auth_headers, mock_graph, "Hello")
        assert resp.status_code == 200
        data = resp.json()
        for field in ("response", "case_id", "pending_docs", "case_status"):
            assert field in data, f"Missing field: {field}"

    def test_blocked_message_returns_200_with_block_text(self, client, auth_headers, mock_graph):
        with patch("guardrails.runner.check_input",
                   new=AsyncMock(return_value=(False, "I can only assist with insurance queries."))):
            resp = client.post("/chat/", json={"message": "What is the weather?"}, headers=auth_headers)
        assert resp.status_code == 200
        assert "insurance" in resp.json()["response"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestUploadValidation:

    def _snapshot_with_state(self, mock_graph, pending=None):
        snapshot = MagicMock()
        snapshot.values = {
            "pending_docs": pending or ["FIR Copy"],
            "collected_docs": [],
            "required_docs": pending or ["FIR Copy"],
        }
        mock_graph.get_state.return_value = snapshot
        mock_graph.invoke.return_value = {
            "last_response": "Thank you, received.",
            "pending_docs": [],
            "collected_docs": ["FIR Copy"],
            "case_status": "active",
        }

    def test_upload_jpg_returns_400(self, client, auth_headers, mock_graph):
        self._snapshot_with_state(mock_graph)
        resp = client.post(
            "/upload/",
            files={"file": ("photo.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")},
            data={"case_id": str(uuid.uuid4()), "document_type": "FIR Copy"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]

    def test_upload_docx_returns_400(self, client, auth_headers, mock_graph):
        self._snapshot_with_state(mock_graph)
        resp = client.post(
            "/upload/",
            files={"file": ("letter.docx", io.BytesIO(b"PK\x03\x04"), "application/vnd.openxmlformats")},
            data={"case_id": str(uuid.uuid4()), "document_type": "FIR Copy"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_upload_nonexistent_case_returns_404(self, client, auth_headers, mock_graph):
        snapshot = MagicMock()
        snapshot.values = {}
        mock_graph.get_state.return_value = snapshot
        resp = client.post(
            "/upload/",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"case_id": str(uuid.uuid4()), "document_type": "FIR Copy"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_upload_missing_case_id_returns_422(self, client, auth_headers):
        resp = client.post(
            "/upload/",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"document_type": "FIR Copy"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_upload_missing_document_type_returns_422(self, client, auth_headers):
        resp = client.post(
            "/upload/",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"case_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_upload_missing_file_returns_422(self, client, auth_headers):
        resp = client.post(
            "/upload/",
            data={"case_id": str(uuid.uuid4()), "document_type": "FIR Copy"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_upload_valid_pdf_returns_200(self, client, auth_headers, mock_graph):
        self._snapshot_with_state(mock_graph)
        with patch("agents.doc_processor.DocProcessor.process", return_value={
            "success": True, "document_id": "doc_abc", "message": "Processed."
        }):
            resp = client.post(
                "/upload/",
                files={"file": ("fir.pdf", io.BytesIO(b"%PDF-1.4 sample content"), "application/pdf")},
                data={"case_id": str(uuid.uuid4()), "document_type": "FIR Copy"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "FIR Copy" in data["collected_docs"]


# ═══════════════════════════════════════════════════════════════════════════════
# CASES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasesEndpoints:

    def test_get_cases_empty_list(self, client, auth_headers, mock_graph):
        resp = client.get("/cases/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_case_not_found_returns_404(self, client, auth_headers, mock_graph):
        resp = client.get(f"/cases/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_case_returns_correct_shape(self, client, auth_headers, mock_graph, mock_db):
        case_id = str(uuid.uuid4())
        fake_case = MagicMock()
        fake_case.case_id = case_id
        fake_case.user_id = "user_123"
        fake_case.intent = "motor_claim"
        fake_case.case_status = "active"
        fake_case.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = fake_case

        snapshot = MagicMock()
        snapshot.values = {
            "pending_docs": ["FIR Copy", "RC Book"],
            "collected_docs": [],
            "required_docs": ["FIR Copy", "RC Book"],
        }
        mock_graph.get_state.return_value = snapshot

        resp = client.get(f"/cases/{case_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        for field in ("case_id", "intent", "case_status", "pending_docs", "collected_docs", "total_docs"):
            assert field in data
        assert data["intent"] == "motor_claim"
        assert data["total_docs"] == 2
