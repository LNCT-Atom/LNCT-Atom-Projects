# Integration test for delete endpoint
"""Test the DELETE /resumes/{document_id} endpoint to ensure it removes the document from MongoDB."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.resume_repository import ResumeRepository
from app.repositories.evaluation_repository import EvaluationRepository

client = TestClient(app)

@pytest.fixture
def repo():
    return ResumeRepository()

@pytest.fixture
def eval_repo():
    return EvaluationRepository()

def generate_dummy_resume(email="api_test@example.com", name="API Test User"):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return {
        "profile": {"full_name": name, "email": email, "phone": "1112223333"},
        "metadata": {"file_name": "api_dummy.pdf", "file_hash": "api_dummyhash", "uploaded_at": now.isoformat()},
        "technical_skills": {"technologies": []},
        "education": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

def test_delete_resume_endpoint(repo):
    # Insert dummy resume directly via repository
    dummy = generate_dummy_resume()
    doc_id = repo.upsert_resume(dummy)
    assert isinstance(doc_id, str)

    # Verify it exists via GET endpoint
    get_resp = client.get(f"/api/resumes/{doc_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data.get("profile", {}).get("full_name") == "API Test User"

    # Delete via DELETE endpoint
    del_resp = client.delete(f"/api/resumes/{doc_id}")
    assert del_resp.status_code == 200
    del_json = del_resp.json()
    assert del_json.get("success") is True

    # Ensure GET now returns 404
    get_after = client.get(f"/api/resumes/{doc_id}")
    assert get_after.status_code == 404

    # Also verify repository returns None
    assert repo.get_resume_by_id(doc_id) is None

def test_delete_resume_cascade_evaluations(repo, eval_repo):
    # Insert dummy resume
    dummy = generate_dummy_resume(email="cascade_eval@example.com", name="Cascade Eval Candidate")
    doc_id = repo.upsert_resume(dummy)
    assert isinstance(doc_id, str)

    # Insert an associated evaluation for this candidate
    dummy_eval = {
        "company_id": "test_company_cascade_123",
        "company_name": "Test Cascade Company",
        "candidate_id": doc_id,
        "candidate_name": "Cascade Eval Candidate",
        "candidate_email": "cascade_eval@example.com",
        "overall_status": "FAILED",
        "is_eligible": False,
        "eligibility_status": "FAILED",
    }
    eval_id = eval_repo.save_evaluation(dummy_eval)
    assert isinstance(eval_id, str)

    # Confirm evaluation exists before deletion
    fetched_eval = eval_repo.get_evaluation_by_id(eval_id)
    assert fetched_eval is not None
    assert fetched_eval.get("candidate_id") == doc_id

    # Call DELETE /resumes/{doc_id}
    del_resp = client.delete(f"/api/resumes/{doc_id}")
    assert del_resp.status_code == 200

    # Verify candidate document is gone
    assert repo.get_resume_by_id(doc_id) is None

    # Verify evaluation document is cascade-deleted
    eval_coll = eval_repo.get_collection()
    orphan_eval = eval_coll.find_one({"_id": eval_repo.get_collection().find_one({"_id": eval_id})})
    assert eval_coll.find_one({"candidate_id": doc_id}) is None
    assert eval_coll.find_one({"candidate_email": "cascade_eval@example.com"}) is None

def test_delete_resume_nonexistent():
    # Calling delete on a non-existent 24-character hex ID should return 404
    del_resp = client.delete("/api/resumes/65f1a2b3c4d5e6f7a8b9c0d1")
    assert del_resp.status_code == 404

def test_delete_resume_invalid_id_format():
    # Calling delete on an invalid ObjectId format should return 404, not 500
    del_resp = client.delete("/api/resumes/invalid-format-id")
    assert del_resp.status_code == 404

def test_delete_resume_idempotent_double_delete(repo):
    # Insert dummy resume
    dummy = generate_dummy_resume(email="double_del@example.com", name="Double Delete User")
    doc_id = repo.upsert_resume(dummy)

    # First delete succeeds
    first_del = client.delete(f"/api/resumes/{doc_id}")
    assert first_del.status_code == 200

    # Second delete returns 404
    second_del = client.delete(f"/api/resumes/{doc_id}")
    assert second_del.status_code == 404
