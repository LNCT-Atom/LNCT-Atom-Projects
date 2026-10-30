"""Resume parsing orchestrator service merging deterministic Python extraction and AI extraction."""
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.schemas.resume_schema import (
    ResumeCanonicalSchema,
    ResumeMetadataSchema,
    ParseResumeResponse,
)
from app.services.text_extractor import TextExtractor, TextExtractionError
from app.services.section_detector import SectionDetector
from app.services.deterministic_parser import DeterministicParser
from app.services.ai_extractor import AIExtractor, AIExtractionError
from app.repositories.resume_repository import ResumeRepository, ResumeRepositoryError
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, repository: ResumeRepository = None):
        self.repository = repository or ResumeRepository()

    def process_resume(self, filename: str, file_bytes: bytes) -> ParseResumeResponse:
        """Execute full parsing pipeline:

        1. Text Extraction & File Integrity Checks
        2. Section Detection & Partitioning
        3. Deterministic Parsing (5 sections: Profile, Education, Skills, Certs, Achievements)
        4. AI Extraction (Projects & Experience only)
        5. Schema Validation (Pydantic v2)
        6. MongoDB Persistence (One complete document)
        7. Confirmation & Response
        """
        # 1. Text Extraction & File Integrity Checks
        extraction_res = TextExtractor.extract_text(filename, file_bytes)
        full_text = extraction_res["text"]
        is_scanned = extraction_res["is_scanned"]
        file_hash = extraction_res["file_hash"]
        file_size = extraction_res["file_size"]
        page_count = extraction_res.get("page_count", 1)

        logger.info(
            f"[EXTRACTION] File='{filename}', Size={file_size} bytes, "
            f"Pages={page_count}, Scanned={is_scanned}, TextLength={len(full_text)} chars"
        )

        # Check for duplicate resumes by content hash (only when DEMO_MODE is False)
        if not settings.DEMO_MODE:
            existing_doc = self.repository.find_by_file_hash(file_hash)
            if existing_doc:
                doc_id = str(existing_doc.get("_id", ""))
                clean_doc = {k: v for k, v in existing_doc.items() if k not in ["_id", "created_at"]}
                canonical_obj = ResumeCanonicalSchema(**clean_doc)
                logger.info(f"[DUPLICATE_FOUND] File hash '{file_hash[:12]}...' matches existing document ID={doc_id}")
                return ParseResumeResponse(
                    success=True,
                    message="Your resume has been submitted successfully, and your parsed JSON data has been saved to our database.",
                    saved=True,
                    resume_id=doc_id,
                    status="completed",
                    duplicate=True,
                    data=canonical_obj,
                )

        # 2. Section Detection & Partitioning
        sections = SectionDetector.partition_resume(full_text)
        detected_sections = [sec for sec, content in sections.items() if content.strip()]
        logger.info(
            f"[SECTION_DETECTION] Identified {len(detected_sections)} non-empty sections: {detected_sections}"
        )

        header_text = sections.get("header_profile", "")
        summary_text = sections.get("summary", "")
        education_text = sections.get("education", "")
        skills_text = sections.get("technical_skills", "")
        projects_text = sections.get("projects", "")
        experience_text = sections.get("experience", "")
        certifications_text = sections.get("certifications", "")
        achievements_text = sections.get("achievements", "")

        # 3. DETERMINISTIC EXTRACTION ONLY (AI MUST NOT BE USED HERE)
        profile_data = DeterministicParser.parse_profile(header_text, summary_text, full_text)
        education_data = DeterministicParser.parse_education(education_text, full_text=full_text)
        skills_data = DeterministicParser.parse_technical_skills(skills_text)
        certifications_data = DeterministicParser.parse_certifications(certifications_text, fallback_text=achievements_text)
        achievements_data = DeterministicParser.parse_achievements(achievements_text, fallback_text=certifications_text)

        populated_profile_fields = sum(1 for _, v in profile_data.model_dump().items() if v is not None)
        logger.info(
            f"[DETERMINISTIC_PARSED] Profile: {populated_profile_fields}/8 fields populated | "
            f"Education: {len(education_data)} entries | "
            f"Skills: {len(skills_data.programming_languages)} langs, {len(skills_data.frameworks)} frameworks, "
            f"{len(skills_data.databases)} databases, {len(skills_data.tools)} tools, {len(skills_data.other_skills)} other | "
            f"Certifications: {len(certifications_data)} entries | "
            f"Achievements: {len(achievements_data)} entries"
        )

        # 4. AI EXTRACTION (PROJECTS AND EXPERIENCE ONLY)
        projects_data = []
        experience_data = []
        ai_called = False

        has_ai_content = bool(projects_text.strip() or experience_text.strip())
        logger.info(
            f"[AI_BOUNDARY] ProjectsTextLength={len(projects_text)} chars, "
            f"ExperienceTextLength={len(experience_text)} chars. SendToAI={has_ai_content}"
        )

        if has_ai_content:
            # STRICT REQUIREMENT: Do not catch AI errors and convert into empty lists.
            # Real empty lists are only valid when AI succeeds with no entries or when sections are absent.
            projects_data, experience_data, ai_called = AIExtractor.extract_projects_and_experience(
                projects_text=projects_text,
                experience_text=experience_text,
            )
            logger.info(
                f"[AI_EXTRACTION_COMPLETE] Status=Success, ai_called={ai_called}, "
                f"ParsedProjects={len(projects_data)}, ParsedExperience={len(experience_data)}"
            )

        # 5. Metadata Creation
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata = ResumeMetadataSchema(
            parser_version="1.0",
            status="completed",
            created_at=now_iso,
            parsed_at=now_iso,
            file_name=filename,
            file_hash=file_hash,
            file_size_bytes=file_size,
            ai_called_for_projects_or_experience=ai_called,
            is_scanned_pdf=is_scanned,
        )

        # 6. Merge into ONE Canonical Object & Validate with Pydantic
        canonical_resume = ResumeCanonicalSchema(
            profile=profile_data,
            education=education_data,
            technical_skills=skills_data,
            projects=projects_data,
            experience=experience_data,
            certifications=certifications_data,
            achievements=achievements_data,
            metadata=metadata,
        )
        logger.info("[SCHEMA_VALIDATION] Pydantic canonical schema validated successfully.")

        # 7. Persist as ONE MongoDB document
        try:
            document_id = self.repository.insert_resume(canonical_resume.model_dump())
            logger.info(f"[MONGODB_PERSISTENCE] Successfully inserted resume document with ID={document_id}")
        except Exception as e:
            logger.error(f"[MONGODB_PERSISTENCE_ERROR] Failed to save resume to database: {str(e)}")
            raise ResumeRepositoryError(f"Database persistence failed: {str(e)}")

        return ParseResumeResponse(
            success=True,
            message="Your resume has been submitted successfully, and your parsed JSON data has been saved to our database.",
            saved=True,
            resume_id=document_id,
            status="completed",
            duplicate=False,
            data=canonical_resume,
        )
