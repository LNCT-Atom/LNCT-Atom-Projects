"""Canonical JSON schema for parsed resumes using Pydantic."""
from enum import Enum
from typing import List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator, field_validator
import re


class ExperienceType(str, Enum):
    INTERNSHIP = "internship"
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    OTHER = "other"
    UNKNOWN = "unknown"


class ProfileSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None


class EducationItemSchema(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = None
    percentage: Optional[str] = None
    class_10_percentage: Optional[str] = None
    class_12_percentage: Optional[str] = None
    backlogs: Optional[int] = None

    @field_validator("cgpa", mode="before")
    @classmethod
    def validate_cgpa(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return round(float(v), 2)
        if isinstance(v, str):
            clean_v = v.strip()
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", clean_v)
            if m:
                try:
                    return round(float(m.group(1)), 2)
                except ValueError:
                    return None
        return None

    @field_validator("cgpa_scale", mode="before")
    @classmethod
    def validate_cgpa_scale(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return round(float(v), 2)
        if isinstance(v, str):
            clean_v = v.strip()
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", clean_v)
            if m:
                try:
                    return round(float(m.group(1)), 2)
                except ValueError:
                    return None
        return None


class TechnicalSkillsSchema(BaseModel):
    technologies: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def migrate_categorized_skills(cls, data: Any) -> Any:
        if isinstance(data, dict):
            existing_techs = list(data.get("technologies") or [])
            seen_lower = {t.lower().strip() for t in existing_techs if isinstance(t, str)}
            # If older categorized lists exist, aggregate them into technologies
            for cat_field in ["programming_languages", "frameworks", "databases", "tools", "other_skills"]:
                cat_list = data.get(cat_field) or []
                if isinstance(cat_list, list):
                    for skill in cat_list:
                        if isinstance(skill, str) and skill.strip():
                            s_clean = skill.strip()
                            if s_clean.lower() not in seen_lower:
                                seen_lower.add(s_clean.lower())
                                existing_techs.append(s_clean)
            data["technologies"] = existing_techs
        return data

    @property
    def programming_languages(self) -> List[str]:
        from app.services.deterministic_parser import DeterministicParser
        return [t for t in self.technologies if t.lower() in DeterministicParser.LANGUAGES]

    @property
    def frameworks(self) -> List[str]:
        from app.services.deterministic_parser import DeterministicParser
        return [t for t in self.technologies if t.lower() in DeterministicParser.FRAMEWORKS]

    @property
    def databases(self) -> List[str]:
        from app.services.deterministic_parser import DeterministicParser
        return [t for t in self.technologies if t.lower() in DeterministicParser.DATABASES]

    @property
    def tools(self) -> List[str]:
        from app.services.deterministic_parser import DeterministicParser
        return [t for t in self.technologies if t.lower() in DeterministicParser.TOOLS]

    @property
    def other_skills(self) -> List[str]:
        from app.services.deterministic_parser import DeterministicParser
        known = DeterministicParser.LANGUAGES | DeterministicParser.FRAMEWORKS | DeterministicParser.DATABASES | DeterministicParser.TOOLS
        return [t for t in self.technologies if t.lower() not in known]


class ProjectItemSchema(BaseModel):
    title: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)

    @property
    def technical_skills(self) -> List[str]:
        return self.technologies

    @technical_skills.setter
    def technical_skills(self, value: List[str]):
        self.technologies = value

    @model_validator(mode="before")
    @classmethod
    def migrate_technical_skills(cls, data: Any) -> Any:
        if isinstance(data, dict):
            techs = list(data.get("technologies") or [])
            if not techs and "technical_skills" in data:
                techs = [t for t in (data.get("technical_skills") or []) if isinstance(t, str)]
            data["technologies"] = techs
        return data


class ExperienceItemSchema(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    experience_type: ExperienceType = ExperienceType.UNKNOWN
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)

    @property
    def technical_skills(self) -> List[str]:
        return self.technologies

    @technical_skills.setter
    def technical_skills(self, value: List[str]):
        self.technologies = value

    @model_validator(mode="before")
    @classmethod
    def migrate_technical_skills(cls, data: Any) -> Any:
        if isinstance(data, dict):
            techs = list(data.get("technologies") or [])
            if not techs and "technical_skills" in data:
                techs = [t for t in (data.get("technical_skills") or []) if isinstance(t, str)]
            data["technologies"] = techs
        return data


class CertificationItemSchema(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None
    credential_id: Optional[str] = None


class AchievementItemSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[str] = None


class ResumeMetadataSchema(BaseModel):
    parser_version: str = "1.0"
    status: str = "completed"
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parsed_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_name: Optional[str] = None
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    ai_called_for_projects_or_experience: bool = False
    is_scanned_pdf: bool = False


class ResumeCanonicalSchema(BaseModel):
    profile: ProfileSchema = Field(default_factory=ProfileSchema)
    education: List[EducationItemSchema] = Field(default_factory=list)
    technical_skills: TechnicalSkillsSchema = Field(default_factory=TechnicalSkillsSchema)
    projects: List[ProjectItemSchema] = Field(default_factory=list)
    experience: List[ExperienceItemSchema] = Field(default_factory=list)
    certifications: List[CertificationItemSchema] = Field(default_factory=list)
    achievements: List[AchievementItemSchema] = Field(default_factory=list)
    metadata: ResumeMetadataSchema = Field(default_factory=ResumeMetadataSchema)


class ParseResumeResponse(BaseModel):
    success: bool = True
    message: str = "Your resume has been submitted successfully, and your parsed JSON data has been saved to our database."
    saved: bool = True
    resume_id: str
    document_id: Optional[str] = None
    status: str = "completed"
    duplicate: bool = False
    data: ResumeCanonicalSchema

    @model_validator(mode="after")
    def sync_document_id(self):
        if not self.document_id and self.resume_id:
            self.document_id = self.resume_id
        elif not self.resume_id and self.document_id:
            self.resume_id = self.document_id
        return self
