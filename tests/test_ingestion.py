"""
Phase 3 end-to-end ingestion test — run with:
    venv\Scripts\python tests\test_ingestion.py

Creates a synthetic PDF in memory, runs the full DocProcessor pipeline,
verifies vectors are in ChromaDB, runs a semantic query, then cleans up.
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Create a minimal PDF in memory using reportlab if available,
#    or fall back to a raw PDF byte string ────────────────────────────────────
def make_test_pdf() -> bytes:
    try:
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.setFont("Helvetica", 12)
        y = 750
        lines = [
            "MOTOR INSURANCE POLICY DOCUMENT",
            "Policy Number: MP-2024-98765",
            "Insured: Rahul Sharma",
            "Vehicle: Maruti Swift DZire, MH-02-AB-1234",
            "Sum Insured: Rs. 6,50,000",
            "Deductible: Rs. 2,000 compulsory excess applies.",
            "Premium: Rs. 12,500 per annum",
            "Coverage: Own damage, third party liability, theft.",
            "Claim Process: FIR required for theft and third party claims.",
            "Contact insurer within 48 hours of any accident.",
            "Valid from: 01-Jan-2024 to 31-Dec-2024",
        ]
        for line in lines:
            c.drawString(50, y, line)
            y -= 25
        c.save()
        return buf.getvalue()
    except ImportError:
        # Minimal valid PDF if reportlab not installed
        return (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
            b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
            b"4 0 obj<</Length 120>>stream\nBT /F1 12 Tf 50 750 Td "
            b"(MOTOR INSURANCE POLICY - Deductible Rs 2000 - Vehicle MH02AB1234) Tj ET\nendstream\nendobj\n"
            b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"xref\n0 6\n0000000000 65535 f\n"
            b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n9\n%%EOF"
        )


TEST_USER_ID  = "test-user-phase3"
TEST_CASE_ID  = "test-case-phase3"
TEST_DOC_TYPE = "Insurance Policy"
TEST_FILENAME = "test_policy.pdf"


def run():
    from agents.doc_processor import DocProcessor
    from db.chroma import get_chroma_client, query_user_collection, delete_document_vectors
    from core.embedding_generator import EmbeddingGenerator
    from db.postgres import SessionLocal, Document, User, Case

    print("Generating test PDF...")
    pdf_bytes = make_test_pdf()
    print(f"[PASS] Test PDF created ({len(pdf_bytes)} bytes)")

    # ── 0. Create prerequisite user + case rows (foreign key requirements) ───
    db = SessionLocal()
    try:
        user_row = User(
            user_id=TEST_USER_ID,
            name="Test User Phase3",
            email="phase3@claimpilot.dev",
            password_hash="test_hash",
        )
        case_row = Case(
            case_id=TEST_CASE_ID,
            user_id=TEST_USER_ID,
            intent="motor_claim",
            case_status="active",
        )
        db.add(user_row)
        db.add(case_row)
        db.commit()
        print("[PASS] Test user and case created in PostgreSQL")
    finally:
        db.close()

    # ── 1. Run DocProcessor ──────────────────────────────────────────────────
    print("\nRunning DocProcessor pipeline...")
    processor = DocProcessor()
    result = processor.process(
        file_bytes=pdf_bytes,
        filename=TEST_FILENAME,
        user_id=TEST_USER_ID,
        case_id=TEST_CASE_ID,
        document_type=TEST_DOC_TYPE,
    )

    assert result["success"], f"DocProcessor failed: {result['message']}"
    document_id = result["document_id"]
    print(f"[PASS] DocProcessor succeeded")
    print(f"       document_id  : {document_id}")
    print(f"       chunks stored: {result['chunks_stored']}")
    print(f"       message      : {result['message']}")

    # ── 2. Verify document row in PostgreSQL ─────────────────────────────────
    db = SessionLocal()
    try:
        doc_row = db.query(Document).filter_by(document_id=document_id).first()
        assert doc_row is not None, "Document row not found in PostgreSQL"
        assert doc_row.document_type == TEST_DOC_TYPE
        assert doc_row.user_id == TEST_USER_ID
        print(f"[PASS] PostgreSQL document row verified")
    finally:
        db.close()

    # ── 3. Verify vectors exist in ChromaDB ──────────────────────────────────
    from db.chroma import get_user_collection
    collection = get_user_collection(TEST_USER_ID)
    count = collection.count()
    assert count > 0, "No vectors found in ChromaDB after processing"
    print(f"[PASS] ChromaDB has {count} vectors for this user")

    # ── 4. Semantic query ─────────────────────────────────────────────────────
    print("\nRunning semantic query...")
    embedder = EmbeddingGenerator()
    query_vec = embedder.embed_single("What is the deductible amount?")
    results = query_user_collection(
        user_id=TEST_USER_ID,
        query_embedding=query_vec,
        case_id=TEST_CASE_ID,
        n_results=3,
    )
    docs_returned = results["documents"][0]
    assert len(docs_returned) > 0, "Semantic query returned no results"
    print(f"[PASS] Semantic query returned {len(docs_returned)} chunk(s)")
    print(f"       Top result: \"{docs_returned[0][:80]}...\"")

    # ── 5. Cleanup ────────────────────────────────────────────────────────────
    print("\nCleaning up test data...")
    delete_document_vectors(TEST_USER_ID, document_id)

    # Delete the entire user collection since it was only for testing
    client = get_chroma_client()
    try:
        client.delete_collection(f"user_{TEST_USER_ID}")
    except Exception:
        pass

    db = SessionLocal()
    try:
        db.query(Document).filter_by(document_id=document_id).delete()
        db.query(Case).filter_by(case_id=TEST_CASE_ID).delete()
        db.query(User).filter_by(user_id=TEST_USER_ID).delete()
        db.commit()
    finally:
        db.close()

    print("[PASS] Test data cleaned up")
    print()
    print("RESULT: All Phase 3 ingestion tests passed")


if __name__ == "__main__":
    run()
