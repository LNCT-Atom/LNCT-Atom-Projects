"""Comprehensive tests for Deterministic Evaluation Engine, Company Requirements, and Schema Validation."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.schemas.resume_schema import (
    ResumeCanonicalSchema,
    TechnicalSkillsSchema,
    ProjectItemSchema,
    ExperienceItemSchema,
    EducationItemSchema,
    ProfileSchema,
)
from app.schemas.company_schema import (
    CompanyRequirementSchema,
    CompanyRequirementCreateSchema,
    CompanyInfoSchema,
    EligibilityCriteriaSchema,
    TechnicalSkillsCriteriaSchema,
    ExperienceCriteriaSchema,
    ProjectCriteriaSchema,
)
from app.schemas.evaluation_schema import (
    EvaluationCanonicalSchema,
    EvaluationStatusEnum,
    OverallStatusEnum,
)
from app.services.evaluation_engine import DeterministicEvaluationEngine
from app.services.deterministic_parser import DeterministicParser
from app.main import app


# ==============================================================================
# TEST 1: Candidate JSON Schema & Unified Technologies
# ==============================================================================
def test_candidate_schema_unified_technologies():
    """Verify TechnicalSkillsSchema uses technologies array and migrates legacy categorized skills."""
    # Direct technologies array
    skills = TechnicalSkillsSchema(technologies=["Java", "Python", "React", "MongoDB", "MySQL", "Spring Boot", "Git"])
    dumped = skills.model_dump()
    assert "technologies" in dumped
    assert dumped["technologies"] == ["Java", "Python", "React", "MongoDB", "MySQL", "Spring Boot", "Git"]

    # Backward compatibility: legacy categorized fields are aggregated into technologies
    legacy_data = {
        "programming_languages": ["Python", "Java"],
        "frameworks": ["Spring Boot", "React"],
        "databases": ["MongoDB"],
        "tools": ["Git"],
        "other_skills": ["Data Structures"],
    }
    migrated_skills = TechnicalSkillsSchema(**legacy_data)
    assert "Python" in migrated_skills.technologies
    assert "Spring Boot" in migrated_skills.technologies
    assert "MongoDB" in migrated_skills.technologies
    assert "Git" in migrated_skills.technologies
    assert "Data Structures" in migrated_skills.technologies

    # Property accessors maintain backward compatibility
    assert "Python" in migrated_skills.programming_languages
    assert "React" in migrated_skills.frameworks


def test_project_and_experience_technologies_migration():
    """Verify ProjectItemSchema and ExperienceItemSchema accept technologies and migrate technical_skills."""
    proj = ProjectItemSchema(
        title="Resume Parser",
        description="A resume parsing application.",
        technologies=["Python", "MongoDB", "React"]
    )
    assert proj.technologies == ["Python", "MongoDB", "React"]
    assert proj.technical_skills == ["Python", "MongoDB", "React"]

    # Migration from older technical_skills key
    proj_old = ProjectItemSchema(**{
        "title": "Old Project",
        "technical_skills": ["Java", "Docker"]
    })
    assert proj_old.technologies == ["Java", "Docker"]
    assert proj_old.model_dump()["technologies"] == ["Java", "Docker"]

    # Experience migration
    exp_old = ExperienceItemSchema(**{
        "company": "Tech Corp",
        "role": "Intern",
        "technical_skills": ["Spring Boot", "MySQL"]
    })
    assert exp_old.technologies == ["Spring Boot", "MySQL"]
    assert exp_old.model_dump()["technologies"] == ["Spring Boot", "MySQL"]


# ==============================================================================
# TEST 2: Deterministic Technology Normalization
# ==============================================================================
def test_deterministic_technology_normalization():
    """Verify deterministic normalization equates variations without AI."""
    norm = DeterministicEvaluationEngine.normalize_technology

    # Case variations
    assert norm("Java") == norm("java")
    assert norm("PYTHON") == norm("python")

    # Spacing and punctuation variations
    assert norm("Spring Boot") == norm("SpringBoot")
    assert norm("spring-boot") == norm("Spring Boot")
    assert norm("Mongo DB") == norm("MongoDB")
    assert norm("React.js") == norm("React")
    assert norm("reactjs") == norm("React")
    assert norm("Node.js") == norm("node")
    assert norm("Vue.js") == norm("vue")
    assert norm("Angular.js") == norm("angular")
    assert norm("PostgreSQL") == norm("postgres")
    assert norm("K8s") == norm("Kubernetes")
    assert norm("Amazon Web Services") == norm("AWS")
    assert norm("Google Cloud") == norm("GCP")
    assert norm("C++") == norm("cpp")
    assert norm("C#") == norm("csharp")


# ==============================================================================
# TEST 3: Deterministic Candidate Skills Matching
# ==============================================================================
def test_deterministic_skills_evaluation_matching():
    """Verify mandatory and preferred technology matching percentages and status."""
    candidate = {
        "technical_skills": {"technologies": ["Java", "Spring Boot", "Git"]},
        "projects": [
            {"title": "Portal", "technologies": ["React", "MySQL"]}
        ],
        "experience": [
            {"company": "Acme", "technologies": ["MongoDB"]}
        ]
    }

    company_req = {
        "technical_skills": {
            "mandatory_technologies": ["Java", "SpringBoot"],  # Normalized match with "Spring Boot"
            "preferred_technologies": ["React", "AWS"]
        }
    }

    skills_res = DeterministicEvaluationEngine._evaluate_technical_skills(candidate, company_req)
    assert skills_res.mandatory_skills_status == EvaluationStatusEnum.PASS
    assert skills_res.mandatory_match_percentage == 100.0
    assert "Java" in skills_res.matched_mandatory_technologies
    assert "SpringBoot" in skills_res.matched_mandatory_technologies
    assert len(skills_res.missing_mandatory_technologies) == 0

    assert "React" in skills_res.matched_preferred_technologies
    assert "AWS" in skills_res.missing_preferred_technologies
    assert skills_res.preferred_match_percentage == 50.0


def test_deterministic_skills_evaluation_failure():
    """Verify mandatory technology failure when required skills are missing."""
    candidate = {
        "technical_skills": {"technologies": ["Python", "Flask"]},
        "projects": [],
        "experience": []
    }

    company_req = {
        "technical_skills": {
            "mandatory_technologies": ["Java", "Spring Boot"],
            "preferred_technologies": []
        }
    }

    skills_res = DeterministicEvaluationEngine._evaluate_technical_skills(candidate, company_req)
    assert skills_res.mandatory_skills_status == EvaluationStatusEnum.FAIL
    assert skills_res.mandatory_match_percentage == 0.0
    assert set(skills_res.missing_mandatory_technologies) == {"Java", "Spring Boot"}


# ==============================================================================
# TEST 4: Eligibility Criteria Deterministic Checks
# ==============================================================================
def test_eligibility_evaluation_pass():
    """Verify CGPA, Degree, Branch, and Graduation Year passing rules."""
    candidate = {
        "education": [
            {
                "degree": "B.Tech",
                "specialization": "Computer Science & Engineering",
                "end_year": "2026",
                "cgpa": "8.4"
            }
        ]
    }

    company_req = {
        "eligibility_criteria": {
            "minimum_cgpa": 7.5,
            "required_degree": ["B.Tech", "B.E."],
            "required_branches": ["CSE", "IT"],
            "eligible_graduation_years": [2026, 2027],
            "minimum_class_10_percentage": None,
            "minimum_class_12_percentage": None,
            "backlog_criteria": None
        }
    }

    missing_data = []
    results, status = DeterministicEvaluationEngine._evaluate_eligibility(
        candidate, company_req, missing_data
    )

    assert status == EvaluationStatusEnum.PASS
    crit_map = {r.criterion: r for r in results}
    assert crit_map["minimum_cgpa"].status == EvaluationStatusEnum.PASS
    assert crit_map["required_degree"].status == EvaluationStatusEnum.PASS
    assert crit_map["required_branches"].status == EvaluationStatusEnum.PASS
    assert crit_map["eligible_graduation_years"].status == EvaluationStatusEnum.PASS


def test_eligibility_evaluation_missing_data_returns_unknown():
    """Verify missing candidate data returns UNKNOWN and does not hard-fail."""
    candidate = {
        "education": [
            {
                "degree": "B.Tech",
                # Missing CGPA, branch, and graduation year
            }
        ]
    }

    company_req = {
        "eligibility_criteria": {
            "minimum_cgpa": 7.5,
            "required_degree": ["B.Tech"],
            "required_branches": ["CSE"],
            "eligible_graduation_years": [2026],
            "minimum_class_10_percentage": None,
            "minimum_class_12_percentage": None,
            "backlog_criteria": None
        }
    }

    missing_data = []
    results, status = DeterministicEvaluationEngine._evaluate_eligibility(
        candidate, company_req, missing_data
    )

    assert status == EvaluationStatusEnum.UNKNOWN
    crit_map = {r.criterion: r for r in results}
    assert crit_map["minimum_cgpa"].status == EvaluationStatusEnum.UNKNOWN
    assert crit_map["required_branches"].status == EvaluationStatusEnum.UNKNOWN
    assert crit_map["eligible_graduation_years"].status == EvaluationStatusEnum.UNKNOWN
    assert len(missing_data) >= 3


def test_academic_eligibility_with_three_levels_and_backlog():
    """Verify College CGPA (null institution), Class 10 %, Class 12 % pass, and backlog remains review."""
    candidate = {
        "education": [
            {
                "institution": None,
                "degree": "B.Tech",
                "specialization": "Computer Science",
                "start_year": "2023",
                "end_year": "2027",
                "cgpa": "8.8",
                "percentage": "83.6%",
            },
            {
                "institution": "Secondary) School, Bhopal 2023",
                "degree": "Class XII / Higher Secondary",
                "specialization": None,
                "start_year": "2022",
                "end_year": "2023",
                "cgpa": None,
                "percentage": "88.4%",
            },
            {
                "institution": "Secondary Board School, 2020 -",
                "degree": "Class X / Secondary",
                "specialization": None,
                "start_year": "2020",
                "end_year": "2021",
                "cgpa": None,
                "percentage": "91.2%",
            },
        ]
    }

    company_req = {
        "eligibility_criteria": {
            "minimum_cgpa": 7,
            "required_degree": ["B.Tech"],
            "required_branches": ["CSE", "IT"],
            "eligible_graduation_years": [2026, 2027],
            "minimum_class_10_percentage": 60,
            "minimum_class_12_percentage": 60,
            "backlog_criteria": "0",
        }
    }

    missing_data = []
    results, academic_status = DeterministicEvaluationEngine._evaluate_eligibility(
        candidate, company_req, missing_data
    )

    assert academic_status == EvaluationStatusEnum.PASS
    crit_map = {r.criterion: r for r in results}
    assert crit_map["minimum_cgpa"].status == EvaluationStatusEnum.PASS
    assert crit_map["minimum_cgpa"].actual == "8.8"
    assert crit_map["required_degree"].status == EvaluationStatusEnum.PASS
    assert crit_map["required_branches"].status == EvaluationStatusEnum.PASS
    assert crit_map["eligible_graduation_years"].status == EvaluationStatusEnum.PASS
    assert crit_map["minimum_class_10_percentage"].status == EvaluationStatusEnum.PASS
    assert crit_map["minimum_class_10_percentage"].actual == "91.2%"
    assert crit_map["minimum_class_12_percentage"].status == EvaluationStatusEnum.PASS
    assert crit_map["minimum_class_12_percentage"].actual == "88.4%"
    assert crit_map["backlog_criteria"].status == EvaluationStatusEnum.UNKNOWN


# ==============================================================================
# TEST 5: Complete Evaluation Engine with Explanations
# ==============================================================================
def test_complete_evaluation_generates_valid_schema():
    """Verify full candidate evaluation produces explainable canonical Evaluation JSON."""
    candidate = {
        "profile": {"full_name": "Rahul Sharma", "email": "rahul@example.com"},
        "education": [
            {
                "degree": "B.Tech",
                "specialization": "Information Technology",
                "end_year": "2026",
                "cgpa": "8.2",
            }
        ],
        "technical_skills": {
            "technologies": ["Java", "Spring Boot", "MySQL", "Git"]
        },
        "projects": [
            {
                "title": "Hospital Management",
                "description": "Built backend services with Spring Boot and MySQL microservices.",
                "technologies": ["Java", "Spring Boot", "MySQL"]
            }
        ],
        "experience": [
            {
                "company": "Tech Labs",
                "role": "Java Intern",
                "experience_type": "internship",
                "technologies": ["Java", "Spring Boot"]
            }
        ]
    }

    company_req = {
        "company": {
            "name": "Acme Corp",
            "email": "hr@acme.com",
            "job_role": "Backend Developer",
        },
        "eligibility_criteria": {
            "minimum_cgpa": 7.0,
            "required_degree": ["B.Tech"],
            "required_branches": ["IT", "CSE"],
            "eligible_graduation_years": [2026],
        },
        "technical_skills": {
            "mandatory_technologies": ["Java", "Spring Boot"],
            "preferred_technologies": ["MySQL"]
        },
        "experience_criteria": {
            "internship_required": True,
            "relevant_technologies": ["Java"]
        },
        "project_criteria": {
            "required_technologies": ["Spring Boot"],
            "minimum_relevant_projects": 1,
            "description_keywords": ["microservices"]
        }
    }

    eval_result = DeterministicEvaluationEngine.evaluate(
        candidate=candidate,
        company_req=company_req,
        candidate_id="cand_123",
        company_id="comp_456",
    )

    assert eval_result.candidate_id == "cand_123"
    assert eval_result.company_id == "comp_456"
    assert eval_result.job_role == "Backend Developer"
    assert eval_result.evaluation.overall_status == OverallStatusEnum.PASS
    assert eval_result.evaluation.eligibility_status == EvaluationStatusEnum.PASS
    assert eval_result.evaluation.mandatory_skills_status == EvaluationStatusEnum.PASS
    assert eval_result.evaluation.experience_status == EvaluationStatusEnum.PASS
    assert eval_result.evaluation.project_status == EvaluationStatusEnum.PASS
    assert eval_result.evaluation_metadata.evaluation_method == "deterministic"


# ==============================================================================
# TEST 6: Company & Evaluation API Routes
# ==============================================================================
def test_company_api_routes_crud():
    """Verify company recruitment requirements API endpoints."""
    client = TestClient(app)

    payload = {
        "company": {
            "name": "Test Company",
            "email": "test@company.com",
            "job_role": "Software Engineer",
            "job_type": "Full-time"
        },
        "eligibility_criteria": {
            "minimum_cgpa": 7.0,
            "required_degree": ["B.Tech"],
            "required_branches": ["CSE"],
            "eligible_graduation_years": [2026]
        },
        "technical_skills": {
            "mandatory_technologies": ["Python", "FastAPI"],
            "preferred_technologies": ["Docker"]
        }
    }

    mock_doc = {**payload, "_id": "6adb209a65b75c4ebbf4b801", "id": "6adb209a65b75c4ebbf4b801"}

    with patch("app.repositories.company_repository.CompanyRepository.insert_company", return_value="6adb209a65b75c4ebbf4b801"), \
         patch("app.repositories.company_repository.CompanyRepository.get_company_by_id", return_value=mock_doc), \
         patch("app.repositories.company_repository.CompanyRepository.list_companies", return_value=[mock_doc]):

        # POST /api/companies
        resp_post = client.post("/api/companies", json=payload)
        assert resp_post.status_code == 201
        assert resp_post.json()["success"] is True

        # GET /api/companies
        resp_list = client.get("/api/companies")
        assert resp_list.status_code == 200
        assert resp_list.json()["count"] == 1

        # GET /api/companies/{id}
        resp_get = client.get("/api/companies/6adb209a65b75c4ebbf4b801")
        assert resp_get.status_code == 200
        assert resp_get.json()["company"]["name"] == "Test Company"
