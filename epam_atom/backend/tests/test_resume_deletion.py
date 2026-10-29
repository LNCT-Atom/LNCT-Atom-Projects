# Integration test for resume deletion functionality
"""Ensures that a resume inserted into the database can be deleted via the repository and that the document is no longer retrievable afterwards."""

import pytest
from datetime import datetime, timezone
from app.repositories.resume_repository import ResumeRepository

@pytest.fixture
def repo():
    return ResumeRepository()

def generate_dummy_resume():
    now = datetime.now(timezone.utc)
    return {
        "profile": {"full_name": "Test User", "email": "test@example.com", "phone": "1234567890"},
        "metadata": {"file_name": "dummy.pdf", "file_hash": "dummyhash123", "uploaded_at": now.isoformat()},
        "technical_skills": {"technologies": []},
        "education": [],
        "projects": [],
        "certifications": [],
        "achievements": []
    }

def test_resume_insert_and_delete(repo):
    dummy = generate_dummy_resume()
    doc_id = repo.upsert_resume(dummy)
    assert isinstance(doc_id, str) and doc_id
    fetched = repo.get_resume_by_id(doc_id)
    assert fetched is not None
    assert fetched.get("profile", {}).get("full_name") == "Test User"
    deleted = repo.delete_resume(doc_id)
    assert deleted is True
    after = repo.get_resume_by_id(doc_id)
    assert after is None
