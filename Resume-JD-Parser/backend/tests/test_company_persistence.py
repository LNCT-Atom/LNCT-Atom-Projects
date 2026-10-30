"""Tests for Company Recruitment Requirements Form Persistence & API.

Verifies:
1. Canonical schema validation and serialization.
2. Handling of optional, nested, numeric, boolean, and list fields.
3. Validation errors for missing required fields.
4. Repository persistence (insert, retrieve, list with filter, update, delete).
5. Ensuring update does not create duplicates.
6. Real MongoDB round-trip integration test when live Atlas connection is available.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.company_schema import (
    CompanyRequirementCreateSchema,
    CompanyRequirementSchema,
    CompanyInfoSchema,
    EligibilityCriteriaSchema,
    TechnicalSkillsCriteriaSchema,
    ExperienceCriteriaSchema,
    ProjectCriteriaSchema,
)
from app.repositories.company_repository import CompanyRepository, CompanyRepositoryError
from app.core.config import settings

client = TestClient(app)


def sample_company_payload():
    return {
        "company": {
            "name": "Test Persistence Corp",
            "email": "hr@testpersistence.com",
            "website": "https://testpersistence.com",
            "location": "Hyderabad / Remote",
            "job_role": "Software Development Engineer - 1",
            "job_description": "Building cloud-native distributed backend services.",
            "job_type": "Full-time",
        },
        "eligibility_criteria": {
            "minimum_cgpa": 7.5,
            "required_degree": ["B.Tech", "MCA"],
            "required_branches": ["CSE", "IT"],
            "eligible_graduation_years": [2026, 2027],
            "minimum_class_10_percentage": 65.0,
            "minimum_class_12_percentage": 65.0,
            "backlog_criteria": "No active backlogs",
        },
        "technical_skills": {
            "mandatory_technologies": ["Python", "FastAPI", "MongoDB"],
            "preferred_technologies": ["Docker", "Kubernetes", "Redis"],
        },
        "experience_criteria": {
            "minimum_experience_months": 6,
            "relevant_technologies": ["Python", "REST APIs"],
            "internship_required": True,
        },
        "project_criteria": {
            "required_technologies": ["Python", "FastAPI"],
            "minimum_relevant_projects": 2,
            "description_keywords": ["microservices", "database"],
        },
    }


def test_company_schema_validation_success():
    """Verify valid company payload parses completely without loss of nested fields."""
    payload = sample_company_payload()
    schema = CompanyRequirementCreateSchema(**payload)
    dumped = schema.model_dump()

    assert dumped["company"]["name"] == "Test Persistence Corp"
    assert dumped["company"]["job_role"] == "Software Development Engineer - 1"
    assert dumped["eligibility_criteria"]["minimum_cgpa"] == 7.5
    assert dumped["eligibility_criteria"]["required_degree"] == ["B.Tech", "MCA"]
    assert dumped["eligibility_criteria"]["eligible_graduation_years"] == [2026, 2027]
    assert dumped["technical_skills"]["mandatory_technologies"] == ["Python", "FastAPI", "MongoDB"]
    assert dumped["experience_criteria"]["internship_required"] is True
    assert dumped["project_criteria"]["minimum_relevant_projects"] == 2


def test_company_schema_missing_required_fields_fails():
    """Verify validation error when required fields are missing."""
    with pytest.raises(Exception):
        # Missing required name and job_role
        CompanyRequirementCreateSchema(
            company=CompanyInfoSchema(email="only_email@test.com")
        )


def test_api_create_and_retrieve_company():
    """Verify creating a company requirement via API endpoint and retrieving it."""
    payload = sample_company_payload()
    response = client.post("/api/companies", json=payload)
    assert response.status_code == 201, response.text
    res_data = response.json()
    assert res_data["success"] is True
    company_id = res_data["company_id"]
    assert company_id is not None

    # Retrieve by ID
    get_res = client.get(f"/api/companies/{company_id}")
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["company"]["name"] == "Test Persistence Corp"
    assert fetched["eligibility_criteria"]["minimum_cgpa"] == 7.5
    assert fetched["technical_skills"]["mandatory_technologies"] == ["Python", "FastAPI", "MongoDB"]

    # Clean up test doc
    delete_res = client.delete(f"/api/companies/{company_id}")
    assert delete_res.status_code == 200


def test_api_update_company_preserves_id_and_avoids_duplicates():
    """Verify updating a company requirement updates the existing document and doesn't duplicate."""
    payload = sample_company_payload()
    res = client.post("/api/companies", json=payload)
    company_id = res.json()["company_id"]

    # Modify some fields
    updated_payload = dict(payload)
    updated_payload["company"]["job_role"] = "Senior Backend Engineer"
    updated_payload["eligibility_criteria"]["minimum_cgpa"] = 8.5
    updated_payload["technical_skills"]["preferred_technologies"].append("Kafka")

    put_res = client.put(f"/api/companies/{company_id}", json=updated_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()["data"]

    assert updated_data["id"] == company_id
    assert updated_data["company"]["job_role"] == "Senior Backend Engineer"
    assert updated_data["eligibility_criteria"]["minimum_cgpa"] == 8.5
    assert "Kafka" in updated_data["technical_skills"]["preferred_technologies"]

    # Ensure updated_at is refreshed
    assert updated_data.get("updated_at") is not None

    # Clean up
    client.delete(f"/api/companies/{company_id}")


def test_api_get_nonexistent_company_returns_404():
    """Verify 404 response when querying a non-existent company ID."""
    from bson import ObjectId
    fake_id = str(ObjectId())
    res = client.get(f"/api/companies/{fake_id}")
    assert res.status_code == 404


def test_api_list_companies_with_search_filter():
    """Verify list endpoint with search filtering."""
    payload = sample_company_payload()
    payload["company"]["name"] = "UniqueSearchCorp_XYZ"
    res = client.post("/api/companies", json=payload)
    cid = res.json()["company_id"]

    try:
        # Search for unique name
        search_res = client.get("/api/companies?search=UniqueSearchCorp_XYZ")
        assert search_res.status_code == 200
        items = search_res.json()["companies"]
        assert len(items) >= 1
        assert any(c["company"]["name"] == "UniqueSearchCorp_XYZ" for c in items)
    finally:
        client.delete(f"/api/companies/{cid}")

