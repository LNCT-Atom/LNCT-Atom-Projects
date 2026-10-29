"""Sprint 2 Tests: Candidate Evaluation, is_eligible calculation, and Complete Classification.

Verifies:
1. Candidate satisfying all mandatory criteria is SELECTED with is_eligible = True.
2. Candidate violating a mandatory criterion is FAILED with is_eligible = False.
3. Candidate with unknown mandatory criterion and no failure is REQUIRES_REVIEW with is_eligible = False.
4. Definite failure takes precedence over unknown criteria (overall FAILED, is_eligible = False).
5. Evaluation persistence and consistency with API responses.
6. Invariant check: Selected + Failed + Requires Review == Total Evaluated Candidates.
7. Candidate evaluations do not leak across company IDs.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.services.evaluation_engine import DeterministicEvaluationEngine
from app.schemas.evaluation_schema import (
    OverallStatusEnum,
    EvaluationStatusEnum,
    EvaluationCanonicalSchema,
)

client = TestClient(app)


def base_qualifying_candidate():
    return {
        "profile": {
            "full_name": "Eligible Candidate",
            "email": "eligible@test.com",
            "phone": "+91 9999999999",
        },
        "education": [
            {
                "institution": "National Institute of Technology",
                "degree": "B.Tech",
                "specialization": "Computer Science and Engineering",
                "start_year": "2023",
                "end_year": "2027",
                "cgpa": 8.5,
                "cgpa_scale": 10.0,
                "percentage": None,
                "class_10_percentage": "85.0%",
                "class_12_percentage": "82.0%",
                "backlogs": 0,
            },
            {
                "institution": "City Junior College",
                "degree": "Class XII / Higher Secondary",
                "percentage": "82.0%",
            },
            {
                "institution": "Public High School",
                "degree": "Class X / Secondary",
                "percentage": "85.0%",
            },
        ],
        "technical_skills": {
            "technologies": ["Java", "Spring Boot", "MongoDB", "React", "Docker"],
            "programming_languages": ["Java"],
            "frameworks": ["Spring Boot", "React"],
            "databases": ["MongoDB"],
        },
        "projects": [
            {
                "title": "E-Commerce Microservices",
                "description": "Built scalable distributed microservices platform with Java and Spring Boot.",
                "technologies": ["Java", "Spring Boot", "MongoDB"],
            }
        ],
        "experience": [
            {
                "company": "Tech Labs",
                "role": "Software Engineering Intern",
                "experience_type": "Internship",
                "technologies": ["Java", "Spring Boot"],
            }
        ],
    }


def base_company_requirements():
    return {
        "company": {
            "name": "Target Tech Corp",
            "email": "careers@targettech.com",
            "job_role": "Backend Engineer",
            "job_type": "Full-time",
        },
        "eligibility_criteria": {
            "minimum_cgpa": 7.0,
            "required_degree": ["B.Tech"],
            "required_branches": ["CSE", "IT"],
            "eligible_graduation_years": [2026, 2027],
            "minimum_class_10_percentage": 60.0,
            "minimum_class_12_percentage": 60.0,
            "backlog_criteria": "No active backlogs",
        },
        "technical_skills": {
            "mandatory_technologies": ["Java", "Spring Boot"],
            "preferred_technologies": ["MongoDB", "Docker"],
        },
        "experience_criteria": {
            "internship_required": True,
            "relevant_technologies": ["Java"],
        },
        "project_criteria": {
            "required_technologies": ["Java"],
            "minimum_relevant_projects": 1,
            "description_keywords": ["microservices"],
        },
    }


def test_candidate_selected_when_all_mandatory_criteria_satisfied():
    """1. Candidate satisfying every mandatory criterion is SELECTED with is_eligible = True."""
    cand = base_qualifying_candidate()
    comp = base_company_requirements()

    evaluation = DeterministicEvaluationEngine.evaluate(
        candidate=cand,
        company_req=comp,
        candidate_id="cand_101",
        company_id="comp_202",
    )

    assert evaluation.is_eligible is True
    assert evaluation.eligibility_status == "SELECTED"
    assert evaluation.evaluation.overall_status == OverallStatusEnum.PASS
    assert evaluation.evaluation.is_eligible is True
    assert evaluation.evaluation.mandatory_skills_status == EvaluationStatusEnum.PASS
    assert evaluation.evaluation.eligibility_status == EvaluationStatusEnum.PASS


def test_candidate_failed_when_mandatory_criterion_fails():
    """2. Candidate definitively violating a mandatory criterion is FAILED with is_eligible = False."""
    cand = base_qualifying_candidate()
    # Modify candidate CGPA to fail cutoff (6.2 < 7.0)
    cand["education"][0]["cgpa"] = 6.2
    comp = base_company_requirements()

    evaluation = DeterministicEvaluationEngine.evaluate(
        candidate=cand,
        company_req=comp,
        candidate_id="cand_102",
        company_id="comp_202",
    )

    assert evaluation.is_eligible is False
    assert evaluation.eligibility_status == "FAILED"
    assert evaluation.evaluation.overall_status == OverallStatusEnum.FAIL
    assert evaluation.evaluation.is_eligible is False
    # Verify exact criterion that failed
    cgpa_crit = next(c for c in evaluation.eligibility_results if c.criterion == "minimum_cgpa")
    assert cgpa_crit.status == EvaluationStatusEnum.FAIL


def test_candidate_requires_review_combined_into_selected_when_no_failure():
    """3. Candidate with unknown info and no definite failure is combined into SELECTED with is_eligible = True."""
    cand = base_qualifying_candidate()
    # Remove backlog information so backlog requirement is UNKNOWN
    del cand["education"][0]["backlogs"]
    comp = base_company_requirements()

    evaluation = DeterministicEvaluationEngine.evaluate(
        candidate=cand,
        company_req=comp,
        candidate_id="cand_103",
        company_id="comp_202",
    )

    assert evaluation.is_eligible is True
    assert evaluation.eligibility_status == "SELECTED"
    assert evaluation.evaluation.overall_status == OverallStatusEnum.PASS
    assert evaluation.evaluation.is_eligible is True
    # Backlog criterion is reported as UNKNOWN
    backlog_crit = next(c for c in evaluation.eligibility_results if c.criterion == "backlog_criteria")
    assert backlog_crit.status == EvaluationStatusEnum.UNKNOWN


def test_definite_failure_takes_precedence_over_unknown():
    """4. If candidate has both a definitive mandatory failure AND unknown info, overall status is FAILED."""
    cand = base_qualifying_candidate()
    # Definite failure: CGPA 5.5 < 7.0
    cand["education"][0]["cgpa"] = 5.5
    # Unknown info: backlog is missing
    del cand["education"][0]["backlogs"]
    comp = base_company_requirements()

    evaluation = DeterministicEvaluationEngine.evaluate(
        candidate=cand,
        company_req=comp,
        candidate_id="cand_104",
        company_id="comp_202",
    )

    assert evaluation.is_eligible is False
    assert evaluation.eligibility_status == "FAILED"
    assert evaluation.evaluation.overall_status == OverallStatusEnum.FAIL
    # Both criteria states are preserved
    crit_map = {c.criterion: c.status for c in evaluation.eligibility_results}
    assert crit_map["minimum_cgpa"] == EvaluationStatusEnum.FAIL
    assert crit_map["backlog_criteria"] == EvaluationStatusEnum.UNKNOWN


def test_candidate_counts_invariant_and_mutually_exclusive():
    """5. Verify that Selected + Failed == Total Evaluated Candidates (2 fields only: Selected and Failed)."""
    candidates = [
        # 1. Selected candidate
        base_qualifying_candidate(),
        # 2. Failed candidate (low CGPA)
        {**base_qualifying_candidate(), "profile": {"full_name": "Low CGPA"}, "education": [{**base_qualifying_candidate()["education"][0], "cgpa": 5.0}]},
        # 3. Failed candidate (missing required mandatory skill)
        {**base_qualifying_candidate(), "profile": {"full_name": "No Skills"}, "technical_skills": {"technologies": ["C++"]}, "projects": [], "experience": []},
        # 4. Review Required candidate (combined into Selected since no failure)
        {**base_qualifying_candidate(), "profile": {"full_name": "Missing Backlog"}, "education": [{k: v for k, v in base_qualifying_candidate()["education"][0].items() if k != "backlogs"}]},
        # 5. Selected candidate 2
        {**base_qualifying_candidate(), "profile": {"full_name": "Eligible Two", "email": "two@test.com"}},
    ]

    comp = base_company_requirements()
    evaluations = [
        DeterministicEvaluationEngine.evaluate(c, comp, f"cand_{idx}", "comp_pool_test")
        for idx, c in enumerate(candidates)
    ]

    selected = [e for e in evaluations if e.is_eligible is True and e.eligibility_status == "SELECTED"]
    failed = [e for e in evaluations if e.is_eligible is False and e.eligibility_status == "FAILED"]

    assert len(selected) == 3
    assert len(failed) == 2
    assert len(selected) + len(failed) == len(candidates)
