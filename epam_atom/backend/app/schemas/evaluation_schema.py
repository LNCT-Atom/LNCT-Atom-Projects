"""Canonical Pydantic schema for Deterministic Candidate Evaluation."""
from enum import Enum
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EvaluationStatusEnum(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class OverallStatusEnum(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class CriterionResultSchema(BaseModel):
    criterion: str
    expected: Any = None
    actual: Any = None
    status: EvaluationStatusEnum
    reason: str


class SkillsEvaluationResultSchema(BaseModel):
    matched_mandatory_technologies: List[str] = Field(default_factory=list)
    missing_mandatory_technologies: List[str] = Field(default_factory=list)
    matched_preferred_technologies: List[str] = Field(default_factory=list)
    missing_preferred_technologies: List[str] = Field(default_factory=list)
    mandatory_match_percentage: float = 0.0
    preferred_match_percentage: float = 0.0
    mandatory_skills_status: EvaluationStatusEnum = EvaluationStatusEnum.NOT_APPLICABLE
    preferred_skills_status: EvaluationStatusEnum = EvaluationStatusEnum.NOT_APPLICABLE
    match_details: List[Dict[str, Any]] = Field(default_factory=list)


class EvaluationSummarySchema(BaseModel):
    eligibility_status: EvaluationStatusEnum
    mandatory_skills_status: EvaluationStatusEnum
    experience_status: EvaluationStatusEnum
    project_status: EvaluationStatusEnum
    overall_status: OverallStatusEnum
    is_eligible: bool = False


class EvaluationMetadataSchema(BaseModel):
    evaluation_method: str = "deterministic"
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvaluationCanonicalSchema(BaseModel):
    id: Optional[str] = None
    candidate_id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    company_id: str
    company_name: str
    job_role: str
    is_eligible: bool = False
    eligibility_status: str = "FAILED"
    evaluation: EvaluationSummarySchema
    eligibility_results: List[CriterionResultSchema] = Field(default_factory=list)
    skills_results: SkillsEvaluationResultSchema = Field(default_factory=SkillsEvaluationResultSchema)
    experience_results: List[CriterionResultSchema] = Field(default_factory=list)
    project_results: List[CriterionResultSchema] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)
    evaluation_metadata: EvaluationMetadataSchema = Field(default_factory=EvaluationMetadataSchema)


class EvaluateRequestSchema(BaseModel):
    company_id: str
    candidate_id: Optional[str] = None  # None evaluates all candidates
