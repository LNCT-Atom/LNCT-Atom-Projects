"""Canonical Pydantic schema for Company Recruitment Requirements."""
from typing import List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CompanyInfoSchema(BaseModel):
    name: str = Field(..., description="Company Name")
    email: str = Field(..., description="Company Email")
    website: Optional[str] = Field(None, description="Company Website")
    location: Optional[str] = Field(None, description="Company Location")
    job_role: str = Field(..., description="Job Role / Position")
    job_description: Optional[str] = Field(None, description="Job Description")
    job_type: str = Field(default="Full-time", description="Job Type (Full-time, Internship, Contract, etc.)")


class EligibilityCriteriaSchema(BaseModel):
    minimum_cgpa: Optional[float] = Field(None, description="Minimum CGPA required (e.g. 7.0)")
    required_degree: List[str] = Field(default_factory=list, description="Eligible degrees e.g. ['B.Tech', 'MCA']")
    required_branches: List[str] = Field(default_factory=list, description="Eligible branches e.g. ['CSE', 'IT']")
    eligible_graduation_years: List[int] = Field(default_factory=list, description="Eligible graduation years e.g. [2026, 2027]")
    minimum_class_10_percentage: Optional[float] = Field(None, description="Minimum 10th percentage if required")
    minimum_class_12_percentage: Optional[float] = Field(None, description="Minimum 12th percentage if required")
    backlog_criteria: Optional[str] = Field(None, description="Backlog requirement e.g. 'No active backlogs'")


class TechnicalSkillsCriteriaSchema(BaseModel):
    mandatory_technologies: List[str] = Field(default_factory=list, description="Mandatory technologies required")
    preferred_technologies: List[str] = Field(default_factory=list, description="Preferred technologies")


class ExperienceCriteriaSchema(BaseModel):
    minimum_experience_months: Optional[int] = Field(None, description="Minimum experience in months")
    relevant_technologies: List[str] = Field(default_factory=list, description="Relevant technologies for experience")
    internship_required: Optional[bool] = Field(default=False, description="Whether prior internship is required")


class ProjectCriteriaSchema(BaseModel):
    required_technologies: List[str] = Field(default_factory=list, description="Required technologies in projects")
    minimum_relevant_projects: Optional[int] = Field(None, description="Minimum number of relevant projects")
    description_keywords: List[str] = Field(default_factory=list, description="Keywords expected in project descriptions")


class CompanyRequirementSchema(BaseModel):
    id: Optional[str] = None
    company: CompanyInfoSchema
    eligibility_criteria: EligibilityCriteriaSchema = Field(default_factory=EligibilityCriteriaSchema)
    technical_skills: TechnicalSkillsCriteriaSchema = Field(default_factory=TechnicalSkillsCriteriaSchema)
    experience_criteria: ExperienceCriteriaSchema = Field(default_factory=ExperienceCriteriaSchema)
    project_criteria: ProjectCriteriaSchema = Field(default_factory=ProjectCriteriaSchema)
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CompanyRequirementCreateSchema(BaseModel):
    company: CompanyInfoSchema
    eligibility_criteria: Optional[EligibilityCriteriaSchema] = Field(default_factory=EligibilityCriteriaSchema)
    technical_skills: Optional[TechnicalSkillsCriteriaSchema] = Field(default_factory=TechnicalSkillsCriteriaSchema)
    experience_criteria: Optional[ExperienceCriteriaSchema] = Field(default_factory=ExperienceCriteriaSchema)
    project_criteria: Optional[ProjectCriteriaSchema] = Field(default_factory=ProjectCriteriaSchema)
