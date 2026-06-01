"""
Phase 2 CRUD tests — run with:
    venv\Scripts\python tests\test_db.py

Creates test rows, verifies reads, then cleans up.
Leaves the database empty after running.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import SessionLocal, User, Case, Document, ConversationState
import json

def run():
    db = SessionLocal()
    errors = []

    try:
        # ── 1. Create User ──────────────────────────────────────────────────
        user = User(
            name="Test User",
            email="test@claimpilot.dev",
            password_hash="hashed_password_placeholder",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.user_id, "user_id not generated"
        print(f"[PASS] User created — user_id: {user.user_id}")

        # ── 2. Read User back ───────────────────────────────────────────────
        fetched_user = db.query(User).filter_by(email="test@claimpilot.dev").first()
        assert fetched_user is not None, "User not found"
        assert fetched_user.name == "Test User", "Name mismatch"
        print("[PASS] User read back correctly")

        # ── 3. Create Case linked to User ───────────────────────────────────
        case = Case(
            user_id=user.user_id,
            intent="motor_claim",
            case_status="active",
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        assert case.case_id, "case_id not generated"
        print(f"[PASS] Case created — case_id: {case.case_id}, intent: {case.intent}")

        # ── 4. Create Document linked to Case ───────────────────────────────
        doc = Document(
            case_id=case.case_id,
            user_id=user.user_id,
            filename="fir_copy.pdf",
            document_type="FIR copy",
            chroma_collection_ref=f"user_{user.user_id}",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        assert doc.document_id, "document_id not generated"
        print(f"[PASS] Document created — document_id: {doc.document_id}, type: {doc.document_type}")

        # ── 5. Create ConversationState linked to Case ──────────────────────
        state_payload = {
            "user_id": user.user_id,
            "case_id": case.case_id,
            "intent": "motor_claim",
            "required_docs": ["FIR copy", "RC Book", "Driving Licence"],
            "collected_docs": ["FIR copy"],
            "pending_docs": ["RC Book", "Driving Licence"],
            "conversation_history": [],
            "case_status": "active",
            "is_new_user": False,
            "current_query": None,
            "last_response": None,
        }
        conv_state = ConversationState(
            case_id=case.case_id,
            user_id=user.user_id,
            state_json=json.dumps(state_payload),
        )
        db.add(conv_state)
        db.commit()
        db.refresh(conv_state)
        assert conv_state.state_id, "state_id not generated"
        print(f"[PASS] ConversationState created — state_id: {conv_state.state_id}")

        # ── 6. Verify relationships ─────────────────────────────────────────
        loaded_case = db.query(Case).filter_by(case_id=case.case_id).first()
        assert len(loaded_case.documents) == 1, "Documents relationship broken"
        assert loaded_case.documents[0].filename == "fir_copy.pdf"
        print("[PASS] Case -> Documents relationship verified")

        loaded_user = db.query(User).filter_by(user_id=user.user_id).first()
        assert len(loaded_user.cases) == 1, "Cases relationship broken"
        print("[PASS] User -> Cases relationship verified")

        # ── 7. Verify ConversationState JSON round-trip ─────────────────────
        loaded_state = db.query(ConversationState).filter_by(case_id=case.case_id).first()
        parsed = json.loads(loaded_state.state_json)
        assert parsed["intent"] == "motor_claim"
        assert parsed["collected_docs"] == ["FIR copy"]
        assert parsed["pending_docs"] == ["RC Book", "Driving Licence"]
        print("[PASS] ConversationState JSON round-trip verified")

    except AssertionError as e:
        errors.append(str(e))
        print(f"[FAIL] {e}")

    finally:
        # ── 8. Clean up all test data ───────────────────────────────────────
        db.query(ConversationState).filter(ConversationState.user_id == user.user_id).delete()
        db.query(Document).filter(Document.user_id == user.user_id).delete()
        db.query(Case).filter(Case.user_id == user.user_id).delete()
        db.query(User).filter(User.email == "test@claimpilot.dev").delete()
        db.commit()
        db.close()
        print("[PASS] Test data cleaned up — database is empty")

    print()
    if errors:
        print(f"RESULT: {len(errors)} test(s) FAILED")
        sys.exit(1)
    else:
        print("RESULT: All CRUD tests passed")

if __name__ == "__main__":
    run()
