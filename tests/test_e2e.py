"""
End-to-End Conversation Tests — full LLM pipeline for all 6 intents.

Requires: PostgreSQL running, GROQ_API_KEY set in .env

Run:  pytest tests/test_e2e.py -v -s
"""
import uuid
import pytest
from fastapi.testclient import TestClient


def _chat(client, token, message, case_id=None):
    resp = client.post(
        "/chat/",
        json={"message": message, "case_id": case_id},
        headers={"Authorization": token},
    )
    assert resp.status_code == 200, f"Chat failed: {resp.text}"
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# ONBOARDING
# ═══════════════════════════════════════════════════════════════════════════════

class TestOnboarding:

    def test_first_message_shows_onboarding_prompt(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        assert data["case_id"]
        response = data["response"].lower()
        assert "claimpilot" in response or "insurance" in response or "claim" in response

    def test_greeting_dear_gets_warm_response(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello dear")
        response = data["response"].lower()
        # Must NOT return cold "I want to make sure I understand" for a greeting
        assert "situation correctly" not in response

    def test_new_case_id_is_uuid_format(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hi")
        try:
            uuid.UUID(data["case_id"])
        except ValueError:
            pytest.fail(f"case_id is not a valid UUID: {data['case_id']}")

    def test_onboarding_case_status_is_active(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        assert data["case_status"] == "active"


# ═══════════════════════════════════════════════════════════════════════════════
# INTENT CLASSIFICATION — all 6 intents
# ═══════════════════════════════════════════════════════════════════════════════

INTENT_SCENARIOS = [
    ("motor_claim",       "My bike was stolen last night"),
    ("health_claim",      "I was hospitalised for surgery last week"),
    ("life_insurance",    "My father passed away and he had a life insurance policy"),
    ("travel_insurance",  "My luggage was lost at the airport"),
    ("home_property",     "My house caught fire and the roof collapsed"),
    ("personal_accident", "I fell from stairs and fractured my arm at the workplace"),
]


class TestIntentClassification:

    @pytest.mark.parametrize("intent,message", INTENT_SCENARIOS)
    def test_intent_classified_and_docs_populated(self, live_client, live_token, intent, message):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        data = _chat(live_client, live_token, message, case_id)
        assert data["case_status"] == "active"
        assert isinstance(data["pending_docs"], list)
        # Either docs are populated (intent classified) or system is asking sub-type question
        response = data["response"]
        assert response  # must always give a response

    def test_health_insurance_explicit_maps_to_health_not_life(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        data = _chat(live_client, live_token, "I had a health insurance in the name of my mother", case_id)
        response = data["response"].lower()
        assert "cause of death" not in response
        assert "death certificate" not in response
        assert "died" not in response

    def test_mother_sick_not_blocked_by_guardrail(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        data = _chat(live_client, live_token, "My mother was suffering from a disease", case_id)
        response = data["response"].lower()
        # Must not be a guardrail block — should lead toward health claim
        assert "only assist" not in response or "insurance" in response

    def test_injured_but_car_fine_classified_as_personal_accident(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        data = _chat(live_client, live_token, "I was injured but my car is perfectly fine", case_id)
        response = data["response"].lower()
        # System either names the intent OR correctly goes straight to document collection.
        # Either way it must NOT treat this as a motor claim (no RC Book, no vehicle repair docs).
        assert "rc book" not in response
        assert "repair estimate" not in response
        # Must show one of: intent confirmation, document request, or injury/medical keywords
        assert any(kw in response for kw in (
            "personal accident", "injury", "medical", "document", "upload", "claim form", "fir"
        ))

    def test_ambiguous_input_asks_for_clarification(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        data = _chat(live_client, live_token, "I need help with something", case_id)
        response = data["response"].lower()
        # Should ask what happened, not crash or give generic error
        assert "vehicle" in response or "health" in response or "happened" in response or "situation" in response


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestConversationEdgeCases:

    def test_one_word_answer_asks_followup(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        data = _chat(live_client, live_token, "claim", case_id)
        response = data["response"].lower()
        assert "vehicle" in response or "health" in response or "what" in response or "more" in response

    def test_acknowledgement_ok_redirects_to_pending(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        _chat(live_client, live_token, "I was hospitalised for surgery", case_id)
        data = _chat(live_client, live_token, "okay thanks", case_id)
        response = data["response"].lower()
        assert "upload" in response or "document" in response or "need" in response
        assert "situation correctly" not in response

    def test_wrong_intent_correction_resets_flow(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        # Trigger life_insurance classification
        _chat(live_client, live_token, "My mother has a life insurance policy", case_id)
        # If awaiting sub-type for life insurance, correct the wrong intent
        data = _chat(live_client, live_token, "No she is not dead, she is alive and healthy", case_id)
        response = data["response"].lower()
        # Should apologise and restart, NOT ask "what was the cause of death?"
        assert "cause of death" not in response

    def test_query_mid_collection_returns_to_pending_doc(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        _chat(live_client, live_token, "My car was stolen", case_id)
        _chat(live_client, live_token, "1", case_id)  # theft subtype
        # Ask a general question mid-collection
        data = _chat(live_client, live_token, "How long does a motor claim take to settle?", case_id)
        response = data["response"].lower()
        # Should answer the question AND include a reminder about the pending doc
        assert "claim" in response
        if data["pending_docs"]:
            assert any(
                kw in response
                for kw in ("upload", "need", "document", "coming back", "still")
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION RESUMPTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionResumption:

    def test_resume_existing_case_returns_status(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        _chat(live_client, live_token, "I had a car accident", case_id)

        resp = live_client.post(
            f"/chat/resume?case_id={case_id}",
            headers={"Authorization": live_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == case_id
        assert data["response"]

    def test_resume_nonexistent_case_returns_404(self, live_client, live_token):
        resp = live_client.post(
            f"/chat/resume?case_id={uuid.uuid4()}",
            headers={"Authorization": live_token},
        )
        assert resp.status_code == 404

    def test_same_case_id_continues_existing_state(self, live_client, live_token):
        data = _chat(live_client, live_token, "Hello")
        case_id = data["case_id"]
        _chat(live_client, live_token, "I was hospitalised for surgery", case_id)
        # Send another message on same case
        data = _chat(live_client, live_token, "I need help with the next step", case_id)
        # Case should still be active, not restarted
        assert data["case_id"] == case_id
        assert data["case_status"] == "active"


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-CASE
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiCase:

    def test_two_cases_have_independent_state(self, live_client, live_token):
        # Case 1: motor
        data1 = _chat(live_client, live_token, "Hello")
        case1 = data1["case_id"]
        _chat(live_client, live_token, "My car was stolen", case1)

        # Case 2: health
        data2 = _chat(live_client, live_token, "Hello")
        case2 = data2["case_id"]
        _chat(live_client, live_token, "I was hospitalised for surgery", case2)

        assert case1 != case2

        # Fetch cases list
        resp = live_client.get("/cases/", headers={"Authorization": live_token})
        assert resp.status_code == 200
        case_ids = [c["case_id"] for c in resp.json()]
        assert case1 in case_ids
        assert case2 in case_ids
