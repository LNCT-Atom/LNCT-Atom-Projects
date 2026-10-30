"""Regression and Unit Tests for Semantic Technology Matching System.

Tests cover all 31 specific requirements across 6 categories:
A. Case-insensitive matching (1-6)
B. Full forms and aliases (7-10)
C. Stack inference (11-14)
D. False-match prevention (15-20)
E. Original JSON immutability (21-27)
F. Integration and regression safety (28-31)
"""
import copy
import pytest
from app.services.semantic_matcher import (
    SemanticTechnologyMatcher,
    MatchStatusEnum,
    MatchReasonEnum,
    DictionaryValidationError,
)
from app.services.evaluation_engine import DeterministicEvaluationEngine
from app.schemas.evaluation_schema import EvaluationStatusEnum, OverallStatusEnum


@pytest.fixture
def matcher():
    return SemanticTechnologyMatcher.get_instance()


# ==============================================================================
# SECTION A: Case-Insensitive Matching (1 - 6)
# ==============================================================================
def test_01_sql_matches_lowercase_sql(matcher):
    """1. SQL matches sql."""
    res = matcher.match_single("SQL", "sql")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "sql"


def test_02_uppercase_python_matches_python(matcher):
    """2. PYTHON matches Python."""
    res = matcher.match_single("PYTHON", "Python")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "python"


def test_03_nodejs_case_variations(matcher):
    """3. Node.JS matches node.js."""
    res = matcher.match_single("Node.JS", "node.js")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "node"


def test_04_reactjs_case_and_dots(matcher):
    """4. React.js matches REACTJS."""
    res = matcher.match_single("React.js", "REACTJS")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "react"


def test_05_leading_and_trailing_whitespace(matcher):
    """5. Leading and trailing whitespace does not affect results."""
    res = matcher.match_single("   Python   ", "Python")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "python"

    res2 = matcher.match_single("SQL", "   sql   ")
    assert res2.status == MatchStatusEnum.MATCH
    assert res2.canonical_id == "sql"


def test_06_spacing_and_punctuation_variations(matcher):
    """6. Recognized spacing and punctuation variations resolve correctly."""
    # Spring Boot variations
    assert matcher.match_single("Spring Boot", "spring-boot").status == MatchStatusEnum.MATCH
    assert matcher.match_single("Spring Boot", "SpringBoot").status == MatchStatusEnum.MATCH

    # Node.js variations
    assert matcher.match_single("Node.js", "NodeJS").status == MatchStatusEnum.MATCH
    assert matcher.match_single("Node.js", "Node JS").status == MatchStatusEnum.MATCH

    # C++ and C# punctuation preserved
    assert matcher.match_single("C++", "c++").status == MatchStatusEnum.MATCH
    assert matcher.match_single("C#", "c#").status == MatchStatusEnum.MATCH


# ==============================================================================
# SECTION B: Full Forms and Aliases (7 - 10)
# ==============================================================================
def test_07_sql_matches_structured_query_language(matcher):
    """7. SQL matches Structured Query Language."""
    res = matcher.match_single("SQL", "Structured Query Language")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "sql"
    assert res.reason == MatchReasonEnum.FULL_FORM_MATCH


def test_08_structured_query_language_matches_sql(matcher):
    """8. Structured Query Language matches SQL."""
    res = matcher.match_single("Structured Query Language", "SQL")
    assert res.status == MatchStatusEnum.MATCH
    assert res.canonical_id == "sql"
    assert res.reason == MatchReasonEnum.FULL_FORM_MATCH


def test_09_nodejs_recognized_aliases(matcher):
    """9. Node.js matches recognized aliases such as NodeJS and Node JS."""
    res1 = matcher.match_single("Node.js", "NodeJS")
    assert res1.status == MatchStatusEnum.MATCH
    assert res1.canonical_id == "node"

    res2 = matcher.match_single("Node.js", "Node JS")
    assert res2.status == MatchStatusEnum.MATCH
    assert res2.canonical_id == "node"


def test_10_unambiguous_shorthand_resolution(matcher):
    """10. Recognized shorthand resolves correctly only when its meaning is unambiguous."""
    # AWS -> Amazon Web Services
    res_aws = matcher.match_single("AWS", "Amazon Web Services")
    assert res_aws.status == MatchStatusEnum.MATCH
    assert res_aws.reason == MatchReasonEnum.FULL_FORM_MATCH

    # GCP -> Google Cloud Platform
    res_gcp = matcher.match_single("GCP", "Google Cloud Platform")
    assert res_gcp.status == MatchStatusEnum.MATCH
    assert res_gcp.reason == MatchReasonEnum.FULL_FORM_MATCH

    # K8s -> Kubernetes
    res_k8s = matcher.match_single("K8s", "Kubernetes")
    assert res_k8s.status == MatchStatusEnum.MATCH
    assert res_k8s.canonical_id == "kubernetes"


# ==============================================================================
# SECTION C: Stack Inference (11 - 14)
# ==============================================================================
def test_11_mern_complete_stack_inference(matcher):
    """11. MERN matches when MongoDB, Express.js, React, and Node.js are independently supported."""
    candidate_skills = ["MongoDB", "Express.js", "React", "Node.js"]
    res = matcher.match_requirement("MERN Stack", candidate_skills)
    assert res.status == MatchStatusEnum.MATCH
    assert res.reason == MatchReasonEnum.STACK_INFERENCE_MATCH
    assert res.canonical_id == "mern"


def test_12_mern_missing_component_prevents_inference(matcher):
    """12. A missing MERN component prevents complete stack inference."""
    # Node.js is missing
    candidate_skills = ["MongoDB", "Express.js", "React"]
    res = matcher.match_requirement("MERN Stack", candidate_skills)
    assert res.status == MatchStatusEnum.NO_MATCH
    assert res.reason == MatchReasonEnum.MISSING_REQUIRED_STACK_COMPONENT
    assert "Node.js" in res.missing_components


def test_13_mern_component_order_does_not_affect_result(matcher):
    """13. Component order does not affect the result."""
    # Reverse / permuted order with various alias forms
    cand1 = ["React.js", "NodeJS", "MongoDB", "ExpressJS"]
    cand2 = ["Node.js", "MongoDB", "Express.js", "React"]
    cand3 = ["Express", "React", "Node", "MongoDB"]

    res1 = matcher.match_requirement("MERN", cand1)
    res2 = matcher.match_requirement("MERN", cand2)
    res3 = matcher.match_requirement("MERN", cand3)

    assert res1.status == MatchStatusEnum.MATCH
    assert res1.reason == MatchReasonEnum.STACK_INFERENCE_MATCH

    assert res2.status == MatchStatusEnum.MATCH
    assert res2.reason == MatchReasonEnum.STACK_INFERENCE_MATCH

    assert res3.status == MatchStatusEnum.MATCH
    assert res3.reason == MatchReasonEnum.STACK_INFERENCE_MATCH


def test_14_ambiguous_component_prevents_stack_match(matcher):
    """14. Ambiguous component names do not automatically establish a stack match."""
    # If candidate has MongoDB, Express, React, but uses an ambiguous token instead of Node
    candidate_skills = ["MongoDB", "Express.js", "React", "ambiguous_token"]
    res = matcher.match_requirement("MERN Stack", candidate_skills)
    assert res.status == MatchStatusEnum.NO_MATCH
    assert res.reason == MatchReasonEnum.MISSING_REQUIRED_STACK_COMPONENT
    assert "Node.js" in res.missing_components


# ==============================================================================
# SECTION D: False-Match Prevention (15 - 20)
# ==============================================================================
def test_15_java_does_not_match_javascript(matcher):
    """15. Java does not match JavaScript."""
    res = matcher.match_single("Java", "JavaScript")
    assert res.status == MatchStatusEnum.NO_MATCH
    assert res.reason == MatchReasonEnum.RELATED_BUT_NOT_EQUIVALENT


def test_16_mysql_not_unconditional_alias_for_sql(matcher):
    """16. MySQL is not an unconditional alias for generic SQL."""
    res = matcher.match_single("SQL", "MySQL")
    assert res.status == MatchStatusEnum.NO_MATCH
    assert res.canonical_id == "sql"
    assert res.matched_canonical_id == "mysql"


def test_17_unknown_technologies_not_automatically_accepted(matcher):
    """17. Unknown technologies are not automatically accepted."""
    res = matcher.match_single("UnlistedFrameworkXYZ", "UnlistedToolABC")
    assert res.status == MatchStatusEnum.NO_MATCH
    assert res.reason == MatchReasonEnum.UNKNOWN_TERM


def test_18_ambiguous_aliases_return_review_required(matcher):
    """18. Ambiguous aliases return REVIEW_REQUIRED."""
    res = matcher.match_single("ambiguous_token", "Python")
    assert res.status == MatchStatusEnum.REVIEW_REQUIRED
    assert res.reason == MatchReasonEnum.AMBIGUOUS_ALIAS


def test_19_conflicting_dictionary_aliases_detected():
    """19. Conflicting dictionary aliases are detected on load."""
    conflicting_dict = {
        "technologies": [
            {"id": "tech_a", "display_name": "Tech A", "aliases": ["shared_alias"]},
            {"id": "tech_b", "display_name": "Tech B", "aliases": ["shared_alias"]},
        ],
        "stacks": []
    }
    with pytest.raises(DictionaryValidationError) as exc_info:
        SemanticTechnologyMatcher(data=conflicting_dict)
    assert "Conflicting alias 'shared_alias'" in str(exc_info.value)


def test_20_fuzzy_suggestions_do_not_automatically_prove_equivalence(matcher):
    """20. Fuzzy suggestions do not automatically prove equivalence."""
    # Typo 'pythn' suggests 'python' but must not silently grant MATCH
    res = matcher.match_single("Python", "pythn")
    assert res.status == MatchStatusEnum.REVIEW_REQUIRED
    assert res.reason == MatchReasonEnum.FUZZY_SUGGESTION_REVIEW
    assert "python" in [s.lower() for s in res.suggested_corrections]


# ==============================================================================
# SECTION E: Original JSON Immutability (21 - 27)
# ==============================================================================
@pytest.fixture
def sample_candidate_and_company():
    candidate = {
        "profile": {"full_name": "Ananya Sharma", "email": "ananya@example.com"},
        "technical_skills": {
            "technologies": ["Structured Query Language", "Python", "MongoDB", "Express.js", "React", "Node.js"],
            "programming_languages": ["Python"],
        },
        "projects": [
            {
                "title": "Cloud Dashboard",
                "technologies": ["React.js", "AWS"],
            }
        ],
        "experience": [
            {
                "company": "Tech Labs",
                "technologies": ["Node.JS"],
            }
        ],
        "education": [
            {
                "degree": "B.Tech",
                "specialization": "Computer Science & Engineering",
                "cgpa": "8.5",
                "end_year": "2026",
            }
        ]
    }

    company_req = {
        "company": {
            "name": "Global Tech Innovations",
            "job_role": "Full Stack Engineer",
        },
        "technical_skills": {
            "mandatory_technologies": ["SQL", "MERN Stack"],
            "preferred_technologies": ["AWS", "Docker"],
        },
        "eligibility_criteria": {
            "minimum_cgpa": 7.0,
            "required_degree": ["B.Tech"],
            "required_branches": ["CSE"],
            "eligible_graduation_years": [2026],
        }
    }
    return candidate, company_req


def test_21_to_27_original_json_immutability(sample_candidate_and_company):
    """21-27. Rigorous verification that original JSON objects remain strictly immutable."""
    candidate, company_req = sample_candidate_and_company

    # Deep copies before evaluation
    candidate_before = copy.deepcopy(candidate)
    company_before = copy.deepcopy(company_req)

    # 1. Run evaluation through DeterministicEvaluationEngine
    eval_result = DeterministicEvaluationEngine.evaluate(
        candidate=candidate,
        company_req=company_req,
        candidate_id="cand_test_001",
        company_id="comp_test_001",
    )

    # 21. Original candidate skill capitalization remains unchanged
    assert candidate["technical_skills"]["technologies"][0] == "Structured Query Language"
    assert candidate["projects"][0]["technologies"][0] == "React.js"
    assert candidate["experience"][0]["technologies"][0] == "Node.JS"

    # 22. Original candidate skill lists remain unchanged (length and items)
    assert len(candidate["technical_skills"]["technologies"]) == len(candidate_before["technical_skills"]["technologies"])
    assert candidate["technical_skills"]["technologies"] == candidate_before["technical_skills"]["technologies"]

    # 23. Original company requirement capitalization remains unchanged
    assert company_req["technical_skills"]["mandatory_technologies"][0] == "SQL"
    assert company_req["technical_skills"]["mandatory_technologies"][1] == "MERN Stack"

    # 24. Original candidate JSON is unchanged after matching
    assert candidate == candidate_before

    # 25. Original company JSON is unchanged after matching
    assert company_req == company_before

    # 26. Source evidence and displayed names remain preserved
    assert candidate["profile"]["full_name"] == "Ananya Sharma"
    assert company_req["company"]["name"] == "Global Tech Innovations"

    # 27. Repeated matching calls do not progressively modify either input
    for _ in range(5):
        _ = DeterministicEvaluationEngine.evaluate(
            candidate=candidate,
            company_req=company_req,
            candidate_id="cand_test_001",
            company_id="comp_test_001",
        )
        assert candidate == candidate_before
        assert company_req == company_before

    # Evaluation results verification
    assert eval_result.evaluation.mandatory_skills_status == EvaluationStatusEnum.PASS
    assert "SQL" in eval_result.skills_results.matched_mandatory_technologies
    assert "MERN Stack" in eval_result.skills_results.matched_mandatory_technologies


# ==============================================================================
# SECTION F: Integration and Regression Safety (28 - 31)
# ==============================================================================
def test_28_existing_recruitment_evaluation_continues_to_pass():
    """28. Existing recruitment evaluation tests continue to pass."""
    candidate = {
        "technical_skills": {"technologies": ["Java", "Spring Boot", "Git"]},
        "projects": [{"title": "Portal", "technologies": ["React", "MySQL"]}],
        "experience": [{"company": "Acme", "technologies": ["MongoDB"]}],
    }
    company_req = {
        "technical_skills": {
            "mandatory_technologies": ["Java", "SpringBoot"],
            "preferred_technologies": ["React", "AWS"],
        }
    }
    skills_res = DeterministicEvaluationEngine._evaluate_technical_skills(candidate, company_req)
    assert skills_res.mandatory_skills_status == EvaluationStatusEnum.PASS
    assert skills_res.mandatory_match_percentage == 100.0
    assert "Java" in skills_res.matched_mandatory_technologies
    assert "SpringBoot" in skills_res.matched_mandatory_technologies
    assert len(skills_res.missing_mandatory_technologies) == 0


def test_29_api_and_schemas_compatibility(sample_candidate_and_company):
    """29. Existing API responses and database schemas remain compatible."""
    candidate, company_req = sample_candidate_and_company
    eval_result = DeterministicEvaluationEngine.evaluate(
        candidate=candidate,
        company_req=company_req,
        candidate_id="cand_test_001",
        company_id="comp_test_001",
    )
    dumped = eval_result.model_dump()
    assert "skills_results" in dumped
    assert "matched_mandatory_technologies" in dumped["skills_results"]
    assert "missing_mandatory_technologies" in dumped["skills_results"]
    assert "match_details" in dumped["skills_results"]
    assert isinstance(dumped["skills_results"]["match_details"], list)


def test_30_unrelated_resume_parsing_and_placement_unimpaired():
    """30. Unrelated resume parsing and placement functionality remains unchanged."""
    from app.services.deterministic_parser import DeterministicParser
    parsed_skills = DeterministicParser.parse_technical_skills("Java, Python, C++, Docker")
    assert "Java" in parsed_skills.technologies
    assert "Python" in parsed_skills.technologies
    assert "C++" in parsed_skills.technologies
    assert "Docker" in parsed_skills.technologies


def test_31_semantic_matcher_connected_to_actual_evaluation_flow(sample_candidate_and_company):
    """31. The semantic matcher is connected to the actual evaluation flow."""
    candidate, company_req = sample_candidate_and_company
    # Candidate lists 'Structured Query Language', company requires 'SQL'
    # Candidate independently lists Mongo, Express, React, Node; company requires 'MERN Stack'
    eval_result = DeterministicEvaluationEngine.evaluate(
        candidate=candidate,
        company_req=company_req,
        candidate_id="cand_flow_01",
        company_id="comp_flow_01",
    )
    assert eval_result.evaluation.mandatory_skills_status == EvaluationStatusEnum.PASS
    assert eval_result.evaluation.overall_status == OverallStatusEnum.PASS
    assert "SQL" in eval_result.skills_results.matched_mandatory_technologies
    assert "MERN Stack" in eval_result.skills_results.matched_mandatory_technologies
    assert len(eval_result.skills_results.missing_mandatory_technologies) == 0

    # Verify explainable match reasons are present in match_details
    reasons = [d["reason"] for d in eval_result.skills_results.match_details]
    assert MatchReasonEnum.FULL_FORM_MATCH in reasons
    assert MatchReasonEnum.STACK_INFERENCE_MATCH in reasons
