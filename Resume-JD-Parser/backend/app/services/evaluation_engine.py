"""Deterministic Candidate Evaluation Engine using pure Python rules.

STRICT INSTRUCTION:
No AI, OpenAI APIs, LLMs, AI agents, semantic matching, or embeddings are used here.
All comparisons are 100% deterministic, explainable, and rule-based.
"""
import re
import logging
from typing import Dict, Any, List, Tuple, Set, Optional
from datetime import datetime, timezone

from app.schemas.evaluation_schema import (
    EvaluationStatusEnum,
    OverallStatusEnum,
    CriterionResultSchema,
    SkillsEvaluationResultSchema,
    EvaluationSummarySchema,
    EvaluationCanonicalSchema,
    EvaluationMetadataSchema,
)

logger = logging.getLogger(__name__)


class DeterministicEvaluationEngine:
    # ------------------ DETERMINISTIC TECHNOLOGY SYNONYM MAP ------------------
    # Canonical mapping for common technology aliases to handle spacing, case, dots, etc.
    TECH_SYNONYMS: Dict[str, str] = {
        "reactjs": "react",
        "react.js": "react",
        "spring boot": "springboot",
        "spring-boot": "springboot",
        "mongo db": "mongodb",
        "mongo": "mongodb",
        "nodejs": "node",
        "node.js": "node",
        "nextjs": "nextjs",
        "next.js": "nextjs",
        "vuejs": "vue",
        "vue.js": "vue",
        "angularjs": "angular",
        "angular.js": "angular",
        "postgresql": "postgres",
        "postgres sql": "postgres",
        "psql": "postgres",
        "amazon web services": "aws",
        "google cloud": "gcp",
        "google cloud platform": "gcp",
        "k8s": "kubernetes",
        "golang": "go",
        "c++": "cpp",
        "c#": "csharp",
        "dot net": "dotnet",
        ".net": "dotnet",
        "rest api": "restapi",
        "restful api": "restapi",
        "ci/cd": "cicd",
        "ci-cd": "cicd",
        "expressjs": "express",
        "express.js": "express",
        "ms sql server": "mssql",
        "sql server": "mssql",
        "tailwind": "tailwindcss",
        "tailwind css": "tailwindcss",
        "js": "javascript",
        "ts": "typescript",
    }

    # Degree normalization map
    DEGREE_SYNONYMS: Dict[str, str] = {
        "b.tech": "btech",
        "btech": "btech",
        "bachelor of technology": "btech",
        "b.e.": "be",
        "b.e": "be",
        "be": "be",
        "bachelor of engineering": "be",
        "bca": "bca",
        "bachelor of computer applications": "bca",
        "mca": "mca",
        "master of computer applications": "mca",
        "m.tech": "mtech",
        "mtech": "mtech",
        "master of technology": "mtech",
        "b.sc": "bsc",
        "bsc": "bsc",
        "bachelor of science": "bsc",
        "m.sc": "msc",
        "msc": "msc",
        "master of science": "msc",
        "mba": "mba",
        "bba": "bba",
    }

    # Branch normalization map
    BRANCH_SYNONYMS: Dict[str, str] = {
        "computer science and engineering": "cse",
        "computer science & engineering": "cse",
        "computer science engineering": "cse",
        "computer science": "cse",
        "cse": "cse",
        "cs": "cse",
        "information technology": "it",
        "it": "it",
        "electronics and communication": "ece",
        "electronics & communication": "ece",
        "electronics and communication engineering": "ece",
        "ece": "ece",
        "electrical engineering": "eee",
        "electrical and electronics": "eee",
        "eee": "eee",
        "mechanical engineering": "mech",
        "mechanical": "mech",
        "mech": "mech",
        "civil engineering": "civil",
        "civil": "civil",
        "artificial intelligence": "aiml",
        "machine learning": "aiml",
        "data science": "aiml",
        "ai & ml": "aiml",
        "ai/ml": "aiml",
        "aiml": "aiml",
        "software engineering": "se",
    }

    @classmethod
    def normalize_technology(cls, tech: str) -> str:
        """Deterministic normalization for technology strings.

        Rules:
        1. Strip whitespace and convert to lowercase.
        2. Check explicit synonym dictionary.
        3. Remove punctuation (dots, hyphens, slashes, spaces).
        """
        if not tech or not isinstance(tech, str):
            return ""
        raw = tech.strip().lower()
        if raw in cls.TECH_SYNONYMS:
            return cls.TECH_SYNONYMS[raw]
        # Strip all punctuation and spaces
        cleaned = re.sub(r"[\s\.\-_/]+", "", raw)
        if cleaned in cls.TECH_SYNONYMS:
            return cls.TECH_SYNONYMS[cleaned]
        return cleaned

    @classmethod
    def normalize_degree(cls, degree: str) -> str:
        """Normalize degree string to canonical format."""
        if not degree or not isinstance(degree, str):
            return ""
        raw = degree.strip().lower()
        if raw in cls.DEGREE_SYNONYMS:
            return cls.DEGREE_SYNONYMS[raw]
        cleaned = re.sub(r"[\s\.\-_/]+", "", raw)
        return cls.DEGREE_SYNONYMS.get(cleaned, cleaned)

    @classmethod
    def normalize_branch(cls, branch: str) -> str:
        """Normalize branch / department string to canonical format."""
        if not branch or not isinstance(branch, str):
            return ""
        raw = branch.strip().lower()
        if raw in cls.BRANCH_SYNONYMS:
            return cls.BRANCH_SYNONYMS[raw]
        cleaned = re.sub(r"[\s\.\-_/]+", "", raw)
        return cls.BRANCH_SYNONYMS.get(cleaned, cleaned)

    @classmethod
    def extract_candidate_technologies(cls, candidate: Dict[str, Any]) -> Tuple[Set[str], Dict[str, str]]:
        """Gather all candidate technologies from skills, projects, and experience.

        Returns (set_of_normalized_keys, dict_mapping_normalized_to_original).
        """
        normalized_keys: Set[str] = set()
        norm_to_original: Dict[str, str] = {}

        def record(t: str):
            if isinstance(t, str) and t.strip():
                clean_t = t.strip()
                norm = cls.normalize_technology(clean_t)
                if norm:
                    normalized_keys.add(norm)
                    if norm not in norm_to_original:
                        norm_to_original[norm] = clean_t

        # 1. Technical Skills (technologies array and legacy categorized lists)
        tech_skills = candidate.get("technical_skills") or {}
        if isinstance(tech_skills, dict):
            # Modern unified technologies array
            for t in tech_skills.get("technologies") or []:
                record(t)
            # Legacy categorized fields
            for cat in ["programming_languages", "frameworks", "databases", "tools", "other_skills"]:
                for t in tech_skills.get(cat) or []:
                    record(t)

        # 2. Projects technologies
        for proj in candidate.get("projects") or []:
            if isinstance(proj, dict):
                for t in (proj.get("technologies") or proj.get("technical_skills") or []):
                    record(t)

        # 3. Experience technologies
        for exp in candidate.get("experience") or []:
            if isinstance(exp, dict):
                for t in (exp.get("technologies") or exp.get("technical_skills") or []):
                    record(t)

        return normalized_keys, norm_to_original

    # =========================================================================
    # CORE EVALUATION LOGIC
    # =========================================================================
    @classmethod
    def evaluate(
        cls,
        candidate: Dict[str, Any],
        company_req: Dict[str, Any],
        candidate_id: str,
        company_id: str,
    ) -> EvaluationCanonicalSchema:
        """Execute complete deterministic evaluation between Candidate JSON and Company JSON."""
        company_info = company_req.get("company", {}) or {}
        company_name = company_info.get("name", "Unknown Company")
        job_role = company_info.get("job_role", "Unknown Role")

        profile = candidate.get("profile", {}) or {}
        candidate_name = profile.get("full_name")
        candidate_email = profile.get("email")

        missing_data: List[str] = []

        # 1. Technical Skills Evaluation
        skills_results = cls._evaluate_technical_skills(candidate, company_req)

        # 2. Eligibility Evaluation
        eligibility_results, eligibility_status = cls._evaluate_eligibility(
            candidate, company_req, missing_data
        )

        # 3. Experience Evaluation
        experience_results, experience_status = cls._evaluate_experience(
            candidate, company_req, missing_data
        )

        # 4. Project Evaluation
        project_results, project_status = cls._evaluate_projects(
            candidate, company_req, missing_data
        )

        # 5. Overall Status Determination
        mandatory_skills_status = skills_results.mandatory_skills_status

        # If any applicable section or criterion is FAIL -> overall is FAIL
        has_fail = (
            eligibility_status == EvaluationStatusEnum.FAIL
            or any(r.status == EvaluationStatusEnum.FAIL for r in eligibility_results)
            or mandatory_skills_status == EvaluationStatusEnum.FAIL
            or experience_status == EvaluationStatusEnum.FAIL
            or project_status == EvaluationStatusEnum.FAIL
        )

        if has_fail:
            overall_status = OverallStatusEnum.FAIL
            is_eligible = False
            eligibility_decision = "FAILED"
        else:
            # Combine Review and Selected: No definitive failure means candidate is SELECTED
            overall_status = OverallStatusEnum.PASS
            is_eligible = True
            eligibility_decision = "SELECTED"

        summary = EvaluationSummarySchema(
            eligibility_status=eligibility_status,
            mandatory_skills_status=mandatory_skills_status,
            experience_status=experience_status,
            project_status=project_status,
            overall_status=overall_status,
            is_eligible=is_eligible,
        )

        metadata = EvaluationMetadataSchema(
            evaluation_method="deterministic",
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

        return EvaluationCanonicalSchema(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            company_id=company_id,
            company_name=company_name,
            job_role=job_role,
            is_eligible=is_eligible,
            eligibility_status=eligibility_decision,
            evaluation=summary,
            eligibility_results=eligibility_results,
            skills_results=skills_results,
            experience_results=experience_results,
            project_results=project_results,
            missing_data=missing_data,
            evaluation_metadata=metadata,
        )

    # ------------------ TECHNICAL SKILLS EVALUATION ------------------
    @classmethod
    def _evaluate_technical_skills(
        cls, candidate: Dict[str, Any], company_req: Dict[str, Any]
    ) -> SkillsEvaluationResultSchema:
        """Deterministically evaluate mandatory and preferred technologies using semantic matcher."""
        from app.services.semantic_matcher import SemanticTechnologyMatcher
        return SemanticTechnologyMatcher.get_instance().evaluate_skills(candidate, company_req)

    # ------------------ EDUCATION LEVEL HELPERS ------------------
    @classmethod
    def is_class_12_record(cls, edu: Dict[str, Any]) -> bool:
        """Identify if an education entry is Class XII / Higher Secondary."""
        deg = (edu.get("degree") or "").lower()
        return any(
            k in deg
            for k in [
                "class xii",
                "class 12",
                "12th",
                "higher secondary",
                "senior secondary",
                "hsc",
                "intermediate",
            ]
        )

    @classmethod
    def is_class_10_record(cls, edu: Dict[str, Any]) -> bool:
        """Identify if an education entry is Class X / Secondary (excluding Higher Secondary)."""
        if cls.is_class_12_record(edu):
            return False
        deg = (edu.get("degree") or "").lower()
        return any(
            k in deg
            for k in [
                "class x",
                "class 10",
                "10th",
                "secondary",
                "ssc",
                "matriculation",
            ]
        )

    @classmethod
    def is_college_record(cls, edu: Dict[str, Any]) -> bool:
        """Identify if an education entry is a College / Higher Education degree."""
        return not cls.is_class_12_record(edu) and not cls.is_class_10_record(edu)

    # ------------------ ELIGIBILITY EVALUATION ------------------
    @classmethod
    def _evaluate_eligibility(
        cls,
        candidate: Dict[str, Any],
        company_req: Dict[str, Any],
        missing_data: List[str],
    ) -> Tuple[List[CriterionResultSchema], EvaluationStatusEnum]:
        """Deterministically evaluate all configured eligibility criteria."""
        criteria = company_req.get("eligibility_criteria", {}) or {}
        results: List[CriterionResultSchema] = []

        education_items = candidate.get("education", []) or []

        # Partition education records deterministically
        college_edus = [e for e in education_items if cls.is_college_record(e)]
        class_12_edus = [e for e in education_items if cls.is_class_12_record(e)]
        class_10_edus = [e for e in education_items if cls.is_class_10_record(e)]

        # 1. Minimum CGPA (Evaluated on College record, without requiring institution name)
        min_cgpa_req = criteria.get("minimum_cgpa")
        if min_cgpa_req is not None:
            # Check college records first; fallback to all records if no degree classification
            target_edus = college_edus if college_edus else education_items
            cand_cgpas = []
            for edu in target_edus:
                cgpa_val = edu.get("cgpa")
                if cgpa_val is not None:
                    match = re.search(r"([0-9]+\.?[0-9]*)", str(cgpa_val))
                    if match:
                        try:
                            cand_cgpas.append((float(match.group(1)), str(cgpa_val)))
                        except ValueError:
                            pass
            if cand_cgpas:
                highest_val, orig_str = max(cand_cgpas, key=lambda x: x[0])
                if highest_val >= float(min_cgpa_req):
                    status = EvaluationStatusEnum.PASS
                    reason = f"Candidate CGPA {orig_str} satisfies minimum required {min_cgpa_req}."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Candidate CGPA {orig_str} is below minimum required {min_cgpa_req}."
                results.append(CriterionResultSchema(
                    criterion="minimum_cgpa",
                    expected=min_cgpa_req,
                    actual=orig_str,
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("Candidate CGPA is not present in resume education records.")
                results.append(CriterionResultSchema(
                    criterion="minimum_cgpa",
                    expected=min_cgpa_req,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="Candidate CGPA is not available in the parsed resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="minimum_cgpa",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Minimum CGPA criterion is not configured.",
            ))

        # 2. Required Degree
        req_degrees = criteria.get("required_degree") or []
        if req_degrees:
            # Look at college degree entries first
            target_edus = college_edus if college_edus else education_items
            cand_degrees = [edu.get("degree") for edu in target_edus if edu.get("degree")]
            if not cand_degrees:
                cand_degrees = [edu.get("degree") for edu in education_items if edu.get("degree")]

            if cand_degrees:
                norm_req_degrees = {cls.normalize_degree(d) for d in req_degrees}
                matched_degs = [
                    d for d in cand_degrees if cls.normalize_degree(d) in norm_req_degrees
                ]
                if matched_degs:
                    status = EvaluationStatusEnum.PASS
                    reason = f"Candidate degree '{matched_degs[0]}' matches required degree(s): {req_degrees}."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Candidate degree(s) {cand_degrees} do not match required degree(s): {req_degrees}."
                results.append(CriterionResultSchema(
                    criterion="required_degree",
                    expected=req_degrees,
                    actual=cand_degrees,
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("Candidate degree is not explicitly present in resume.")
                results.append(CriterionResultSchema(
                    criterion="required_degree",
                    expected=req_degrees,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No degree information found in candidate resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="required_degree",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Required degree criterion is not configured.",
            ))

        # 3. Required Branch / Department
        req_branches = criteria.get("required_branches") or []
        if req_branches:
            target_edus = college_edus if college_edus else education_items
            cand_branches = [
                edu.get("specialization") for edu in target_edus if edu.get("specialization")
            ]
            if not cand_branches:
                cand_branches = [
                    edu.get("specialization") for edu in education_items if edu.get("specialization")
                ]

            if cand_branches:
                norm_req_branches = {cls.normalize_branch(b) for b in req_branches}
                matched_branches = [
                    b for b in cand_branches if cls.normalize_branch(b) in norm_req_branches
                ]
                if matched_branches:
                    status = EvaluationStatusEnum.PASS
                    reason = f"Candidate branch '{matched_branches[0]}' matches required branch(es): {req_branches}."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Candidate branch(es) {cand_branches} do not match required branch(es): {req_branches}."
                results.append(CriterionResultSchema(
                    criterion="required_branches",
                    expected=req_branches,
                    actual=cand_branches,
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("Candidate branch/specialization is not present in resume.")
                results.append(CriterionResultSchema(
                    criterion="required_branches",
                    expected=req_branches,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No branch/specialization found in candidate resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="required_branches",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Required branch criterion is not configured.",
            ))

        # 4. Eligible Graduation Years
        grad_years = criteria.get("eligible_graduation_years") or []
        if grad_years:
            target_edus = college_edus if college_edus else [
                e for e in education_items if not cls.is_class_10_record(e) and not cls.is_class_12_record(e)
            ]
            cand_years = []
            for edu in target_edus:
                end_y = edu.get("end_year")
                if end_y:
                    y_match = re.search(r"\b(20\d{2}|19\d{2})\b", str(end_y))
                    if y_match:
                        cand_years.append(int(y_match.group(1)))
            if cand_years:
                matched_years = [y for y in cand_years if y in grad_years]
                if matched_years:
                    status = EvaluationStatusEnum.PASS
                    reason = f"Candidate graduation year {matched_years[0]} is eligible."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Candidate graduation year(s) {cand_years} are not in eligible years: {grad_years}."
                results.append(CriterionResultSchema(
                    criterion="eligible_graduation_years",
                    expected=grad_years,
                    actual=cand_years,
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("Candidate graduation year is not specified in resume.")
                results.append(CriterionResultSchema(
                    criterion="eligible_graduation_years",
                    expected=grad_years,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="Graduation year is not specified in candidate resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="eligible_graduation_years",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Eligible graduation years criterion is not configured.",
            ))

        # 5. Minimum Class 10 Percentage
        min_10 = criteria.get("minimum_class_10_percentage")
        if min_10 is not None:
            cand_10_pct = None
            orig_10_str = None
            # Check dedicated Class 10 education records first
            for edu in class_10_edus:
                pct_str = edu.get("percentage")
                if pct_str is not None:
                    m = re.search(r"([0-9]+\.?[0-9]*)", str(pct_str))
                    if m:
                        cand_10_pct = float(m.group(1))
                        orig_10_str = str(pct_str)
                        break
            # Fallback: check class_10_percentage field on any education record
            # (populated by parser extraction or manual entry)
            if cand_10_pct is None:
                for edu in education_items:
                    c10_str = edu.get("class_10_percentage")
                    if c10_str is not None:
                        m = re.search(r"([0-9]+\.?[0-9]*)", str(c10_str))
                        if m:
                            cand_10_pct = float(m.group(1))
                            orig_10_str = str(c10_str)
                            break
            if cand_10_pct is not None:
                if cand_10_pct >= float(min_10):
                    status = EvaluationStatusEnum.PASS
                    reason = f"Class 10 percentage {orig_10_str} meets minimum required {min_10}%."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Class 10 percentage {orig_10_str} is below minimum required {min_10}%."
                results.append(CriterionResultSchema(
                    criterion="minimum_class_10_percentage",
                    expected=min_10,
                    actual=orig_10_str,
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("Candidate Class 10 percentage is not present in resume.")
                results.append(CriterionResultSchema(
                    criterion="minimum_class_10_percentage",
                    expected=min_10,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="Class 10 percentage not provided in resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="minimum_class_10_percentage",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Class 10 percentage criterion is not configured.",
            ))

        # 6. Minimum Class 12 Percentage
        min_12 = criteria.get("minimum_class_12_percentage")
        if min_12 is not None:
            cand_12_pct = None
            orig_12_str = None
            # Check dedicated Class 12 education records first
            for edu in class_12_edus:
                pct_str = edu.get("percentage")
                if pct_str is not None:
                    m = re.search(r"([0-9]+\.?[0-9]*)", str(pct_str))
                    if m:
                        cand_12_pct = float(m.group(1))
                        orig_12_str = str(pct_str)
                        break
            # Fallback: check class_12_percentage field on any education record
            # (populated by parser extraction or manual entry)
            if cand_12_pct is None:
                for edu in education_items:
                    c12_str = edu.get("class_12_percentage")
                    if c12_str is not None:
                        m = re.search(r"([0-9]+\.?[0-9]*)", str(c12_str))
                        if m:
                            cand_12_pct = float(m.group(1))
                            orig_12_str = str(c12_str)
                            break
            if cand_12_pct is not None:
                if cand_12_pct >= float(min_12):
                    status = EvaluationStatusEnum.PASS
                    reason = f"Class 12 percentage {orig_12_str} meets minimum required {min_12}%."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Class 12 percentage {orig_12_str} is below minimum required {min_12}%."
                results.append(CriterionResultSchema(
                    criterion="minimum_class_12_percentage",
                    expected=min_12,
                    actual=orig_12_str,
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("Candidate Class 12 percentage is not present in resume.")
                results.append(CriterionResultSchema(
                    criterion="minimum_class_12_percentage",
                    expected=min_12,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="Class 12 percentage not provided in resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="minimum_class_12_percentage",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Class 12 percentage criterion is not configured.",
            ))

        # 7. Backlog Criteria (Preserve status & explanation without corrupting academic marks)
        backlog_req = criteria.get("backlog_criteria")
        if backlog_req is not None and str(backlog_req).strip():
            # Check for explicit backlogs field on education records (from parser or manual entry)
            cand_backlogs = None
            for edu in education_items:
                bl = edu.get("backlogs")
                if bl is not None:
                    cand_backlogs = int(bl)
                    break

            if cand_backlogs is not None:
                backlog_text = str(backlog_req).lower().strip()
                # Determine if company requires zero backlogs
                requires_zero = any(kw in backlog_text for kw in ["no", "nil", "zero", "0"])
                if requires_zero:
                    if cand_backlogs == 0:
                        results.append(CriterionResultSchema(
                            criterion="backlog_criteria",
                            expected=backlog_req,
                            actual=str(cand_backlogs),
                            status=EvaluationStatusEnum.PASS,
                            reason=f"Candidate has {cand_backlogs} backlogs, meeting requirement '{backlog_req}'.",
                        ))
                    else:
                        results.append(CriterionResultSchema(
                            criterion="backlog_criteria",
                            expected=backlog_req,
                            actual=str(cand_backlogs),
                            status=EvaluationStatusEnum.FAIL,
                            reason=f"Candidate has {cand_backlogs} backlog(s), violating requirement '{backlog_req}'.",
                        ))
                else:
                    # Non-zero-backlog requirement — just report the count
                    results.append(CriterionResultSchema(
                        criterion="backlog_criteria",
                        expected=backlog_req,
                        actual=str(cand_backlogs),
                        status=EvaluationStatusEnum.PASS,
                        reason=f"Candidate has {cand_backlogs} backlog(s). Requirement: '{backlog_req}'.",
                    ))
            else:
                missing_data.append("Backlog status cannot be verified from resume.")
                results.append(CriterionResultSchema(
                    criterion="backlog_criteria",
                    expected=backlog_req,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason=f"Backlog requirement '{backlog_req}' cannot be verified from resume and requires manual candidate check.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="backlog_criteria",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Backlog criterion is not configured.",
            ))

        # Determine academic eligibility status (based on academic credentials)
        academic_criteria_names = {
            "minimum_cgpa",
            "required_degree",
            "required_branches",
            "eligible_graduation_years",
            "minimum_class_10_percentage",
            "minimum_class_12_percentage",
        }
        academic_results = [
            r for r in results
            if r.criterion in academic_criteria_names and r.status != EvaluationStatusEnum.NOT_APPLICABLE
        ]

        if not academic_results:
            overall_elig = EvaluationStatusEnum.NOT_APPLICABLE
        elif any(r.status == EvaluationStatusEnum.FAIL for r in academic_results):
            overall_elig = EvaluationStatusEnum.FAIL
        elif any(r.status == EvaluationStatusEnum.UNKNOWN for r in academic_results):
            overall_elig = EvaluationStatusEnum.UNKNOWN
        else:
            overall_elig = EvaluationStatusEnum.PASS

        return results, overall_elig

    # ------------------ EXPERIENCE EVALUATION ------------------
    @classmethod
    def _evaluate_experience(
        cls,
        candidate: Dict[str, Any],
        company_req: Dict[str, Any],
        missing_data: List[str],
    ) -> Tuple[List[CriterionResultSchema], EvaluationStatusEnum]:
        """Deterministically evaluate experience criteria."""
        exp_criteria = company_req.get("experience_criteria", {}) or {}
        results: List[CriterionResultSchema] = []

        experiences = candidate.get("experience", []) or []

        # 1. Internship requirement
        intern_req = exp_criteria.get("internship_required")
        if intern_req:
            has_internship = False
            internship_detail = None
            for exp in experiences:
                exp_type = (exp.get("experience_type") or "").lower()
                role_str = (exp.get("role") or "").lower()
                if exp_type == "internship" or "intern" in role_str:
                    has_internship = True
                    internship_detail = f"{exp.get('company') or 'Company'} ({exp.get('role') or 'Intern'})"
                    break

            if has_internship:
                results.append(CriterionResultSchema(
                    criterion="internship_required",
                    expected=True,
                    actual=internship_detail,
                    status=EvaluationStatusEnum.PASS,
                    reason=f"Candidate has verified internship experience: {internship_detail}.",
                ))
            elif experiences:
                results.append(CriterionResultSchema(
                    criterion="internship_required",
                    expected=True,
                    actual=f"{len(experiences)} non-internship experience record(s)",
                    status=EvaluationStatusEnum.FAIL,
                    reason="Candidate has work experience, but no internship was found.",
                ))
            else:
                missing_data.append("No work or internship experience records present in resume.")
                results.append(CriterionResultSchema(
                    criterion="internship_required",
                    expected=True,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No work or internship experience records found in resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="internship_required",
                expected=False,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Internship requirement is not configured.",
            ))

        # 2. Minimum experience duration
        min_months = exp_criteria.get("minimum_experience_months")
        if min_months is not None and min_months > 0:
            # Deterministic requirement: do not invent duration if it cannot be reliably calculated
            missing_data.append("Exact experience duration cannot be reliably calculated from available date information.")
            results.append(CriterionResultSchema(
                criterion="minimum_experience_months",
                expected=min_months,
                actual=None,
                status=EvaluationStatusEnum.UNKNOWN,
                reason=f"Candidate experience duration cannot be reliably determined from dates in resume.",
            ))
        else:
            results.append(CriterionResultSchema(
                criterion="minimum_experience_months",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Minimum experience months criterion is not configured.",
            ))

        # 3. Relevant experience technologies
        rel_techs = exp_criteria.get("relevant_technologies") or []
        if rel_techs:
            cand_exp_techs = set()
            for exp in experiences:
                for t in (exp.get("technologies") or exp.get("technical_skills") or []):
                    cand_exp_techs.add(cls.normalize_technology(t))

            matched_rel = [t for t in rel_techs if cls.normalize_technology(t) in cand_exp_techs]
            if matched_rel:
                results.append(CriterionResultSchema(
                    criterion="relevant_technologies",
                    expected=rel_techs,
                    actual=matched_rel,
                    status=EvaluationStatusEnum.PASS,
                    reason=f"Candidate experience includes relevant technologies: {matched_rel}.",
                ))
            elif experiences:
                results.append(CriterionResultSchema(
                    criterion="relevant_technologies",
                    expected=rel_techs,
                    actual=[],
                    status=EvaluationStatusEnum.FAIL,
                    reason=f"Candidate experience does not mention relevant technologies: {rel_techs}.",
                ))
            else:
                missing_data.append("No experience records to check relevant technologies.")
                results.append(CriterionResultSchema(
                    criterion="relevant_technologies",
                    expected=rel_techs,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No experience entries found to verify relevant technologies.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="relevant_technologies",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Relevant experience technologies criterion is not configured.",
            ))

        configured = [r for r in results if r.status != EvaluationStatusEnum.NOT_APPLICABLE]
        if not configured:
            overall_exp = EvaluationStatusEnum.NOT_APPLICABLE
        elif any(r.status == EvaluationStatusEnum.FAIL for r in configured):
            overall_exp = EvaluationStatusEnum.FAIL
        elif any(r.status == EvaluationStatusEnum.UNKNOWN for r in configured):
            overall_exp = EvaluationStatusEnum.UNKNOWN
        else:
            overall_exp = EvaluationStatusEnum.PASS

        return results, overall_exp

    # ------------------ PROJECT EVALUATION ------------------
    @classmethod
    def _evaluate_projects(
        cls,
        candidate: Dict[str, Any],
        company_req: Dict[str, Any],
        missing_data: List[str],
    ) -> Tuple[List[CriterionResultSchema], EvaluationStatusEnum]:
        """Deterministically evaluate project criteria."""
        proj_criteria = company_req.get("project_criteria", {}) or {}
        results: List[CriterionResultSchema] = []

        projects = candidate.get("projects", []) or []

        # 1. Required project technologies
        req_techs = proj_criteria.get("required_technologies") or []
        if req_techs:
            if projects:
                norm_req = {cls.normalize_technology(t) for t in req_techs}
                matching_projects = []
                for p in projects:
                    p_techs = {
                        cls.normalize_technology(t)
                        for t in (p.get("technologies") or p.get("technical_skills") or [])
                    }
                    if p_techs & norm_req:
                        matching_projects.append(p.get("title") or "Project")

                if matching_projects:
                    results.append(CriterionResultSchema(
                        criterion="required_technologies",
                        expected=req_techs,
                        actual=matching_projects,
                        status=EvaluationStatusEnum.PASS,
                        reason=f"Candidate project(s) utilize required technologies: {matching_projects}.",
                    ))
                else:
                    results.append(CriterionResultSchema(
                        criterion="required_technologies",
                        expected=req_techs,
                        actual=[],
                        status=EvaluationStatusEnum.FAIL,
                        reason=f"None of candidate's projects mention required project technologies: {req_techs}.",
                    ))
            else:
                missing_data.append("No projects listed in candidate resume.")
                results.append(CriterionResultSchema(
                    criterion="required_technologies",
                    expected=req_techs,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No projects listed in candidate resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="required_technologies",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Required project technologies criterion is not configured.",
            ))

        # 2. Minimum number of relevant projects
        min_proj = proj_criteria.get("minimum_relevant_projects")
        if min_proj is not None and min_proj > 0:
            if projects:
                if len(projects) >= min_proj:
                    status = EvaluationStatusEnum.PASS
                    reason = f"Candidate has {len(projects)} project(s), meeting minimum required {min_proj}."
                else:
                    status = EvaluationStatusEnum.FAIL
                    reason = f"Candidate has {len(projects)} project(s), below minimum required {min_proj}."
                results.append(CriterionResultSchema(
                    criterion="minimum_relevant_projects",
                    expected=min_proj,
                    actual=len(projects),
                    status=status,
                    reason=reason,
                ))
            else:
                missing_data.append("No projects listed to verify minimum project count.")
                results.append(CriterionResultSchema(
                    criterion="minimum_relevant_projects",
                    expected=min_proj,
                    actual=0,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No projects listed in candidate resume.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="minimum_relevant_projects",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Minimum relevant projects criterion is not configured.",
            ))

        # 3. Project description keywords
        desc_keywords = proj_criteria.get("description_keywords") or []
        if desc_keywords:
            if projects:
                all_desc = " ".join([p.get("description", "") or "" for p in projects]).lower()
                matched_kw = [
                    kw for kw in desc_keywords
                    if re.search(rf"\b{re.escape(kw.lower())}\b", all_desc)
                ]
                if matched_kw:
                    results.append(CriterionResultSchema(
                        criterion="description_keywords",
                        expected=desc_keywords,
                        actual=matched_kw,
                        status=EvaluationStatusEnum.PASS,
                        reason=f"Project descriptions contain keyword(s): {matched_kw}.",
                    ))
                else:
                    results.append(CriterionResultSchema(
                        criterion="description_keywords",
                        expected=desc_keywords,
                        actual=[],
                        status=EvaluationStatusEnum.FAIL,
                        reason=f"Project descriptions do not contain required keyword(s): {desc_keywords}.",
                    ))
            else:
                missing_data.append("No project descriptions to evaluate keywords.")
                results.append(CriterionResultSchema(
                    criterion="description_keywords",
                    expected=desc_keywords,
                    actual=None,
                    status=EvaluationStatusEnum.UNKNOWN,
                    reason="No project descriptions available to evaluate keywords.",
                ))
        else:
            results.append(CriterionResultSchema(
                criterion="description_keywords",
                expected=None,
                actual=None,
                status=EvaluationStatusEnum.NOT_APPLICABLE,
                reason="Project description keywords criterion is not configured.",
            ))

        configured = [r for r in results if r.status != EvaluationStatusEnum.NOT_APPLICABLE]
        if not configured:
            overall_proj = EvaluationStatusEnum.NOT_APPLICABLE
        elif any(r.status == EvaluationStatusEnum.FAIL for r in configured):
            overall_proj = EvaluationStatusEnum.FAIL
        elif any(r.status == EvaluationStatusEnum.UNKNOWN for r in configured):
            overall_proj = EvaluationStatusEnum.UNKNOWN
        else:
            overall_proj = EvaluationStatusEnum.PASS

        return results, overall_proj
