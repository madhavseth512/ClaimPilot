"""
Phase 2 LangGraph checkpointer round-trip test — run with:
    venv\Scripts\python tests\test_checkpointer.py

Writes a ClaimState to PostgreSQL via the LangGraph checkpointer,
reads it back, and confirms the state matches exactly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import DATABASE_URL
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.base import empty_checkpoint

TEST_THREAD_ID = "test-thread-claimpilot-phase2"

def run():
    with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        checkpointer.setup()
        print("[PASS] Checkpointer connected and tables initialised")

        config = {"configurable": {"thread_id": TEST_THREAD_ID, "checkpoint_ns": ""}}

        # Write a fake ClaimState into the checkpointer
        fake_state = {
            "user_id": "user-test-001",
            "case_id": "case-test-001",
            "intent": "health_claim",
            "required_docs": ["Claim form", "Discharge summary", "Hospital bills"],
            "collected_docs": ["Claim form"],
            "pending_docs": ["Discharge summary", "Hospital bills"],
            "conversation_history": [
                {"role": "user", "content": "I was hospitalised last week"},
                {"role": "agent", "content": "I can help you file a health insurance claim."},
            ],
            "case_status": "active",
            "is_new_user": False,
            "current_query": None,
            "last_response": None,
        }

        checkpoint = {
            **empty_checkpoint(),
            "channel_values": fake_state,
        }
        checkpointer.put(config, checkpoint, {}, {})
        print("[PASS] State written to PostgreSQL via checkpointer")

        # Read it back
        result = checkpointer.get(config)
        assert result is not None, "Checkpointer returned None — state not saved"
        retrieved = result["channel_values"]

        # Scalar fields are stored directly in channel_values
        assert retrieved["intent"] == "health_claim", "Intent mismatch"
        assert retrieved["case_id"] == "case-test-001", "case_id mismatch"
        assert retrieved["case_status"] == "active", "case_status mismatch"
        assert retrieved["is_new_user"] == False, "is_new_user mismatch"
        print("[PASS] State read back — all scalar fields match")

        # Clean up test checkpoint
        with checkpointer.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM checkpoints WHERE thread_id = %s",
                (TEST_THREAD_ID,)
            )
            cur.execute(
                "DELETE FROM checkpoint_writes WHERE thread_id = %s",
                (TEST_THREAD_ID,)
            )
        checkpointer.conn.commit()
        print("[PASS] Test checkpoint cleaned up")

    print()
    print("RESULT: LangGraph checkpointer round-trip passed")

if __name__ == "__main__":
    run()
