"""API router for resume parsing and retrieval."""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.resume_schema import ParseResumeResponse
from app.services.resume_service import ResumeService
from app.services.text_extractor import TextExtractionError
from app.services.ai_extractor import AIExtractionError
from app.repositories.resume_repository import ResumeRepositoryError
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])
resume_service = ResumeService()


@router.post("/parse", response_model=ParseResumeResponse, status_code=status.HTTP_200_OK)
async def parse_resume(file: UploadFile = File(...)):
    """Upload a resume in PDF or DOCX format for parsing and storage.

    - Predictable sections (Profile, Education, Skills, Certifications, Achievements) are parsed deterministically using Python.
    - Projects and Experience are isolated and extracted using OpenAI.
    - All sections are merged into one canonical JSON object and saved to MongoDB.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded or filename is missing.",
        )

    # Read uploaded file content safely
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file.",
        )

    # Enforce maximum upload size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    try:
        response = resume_service.process_resume(
            filename=file.filename,
            file_bytes=file_bytes,
        )
        return response
    except TextExtractionError as te:
        logger.warning(f"File validation or extraction failure: {str(te)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(te),
        )
    except AIExtractionError as ae:
        logger.error(f"AI extraction failure for projects/experience: {str(ae)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI extraction failed: {str(ae)}",
        )
    except ResumeRepositoryError as re:
        logger.error(f"Database persistence error: {str(re)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database persistence error: {str(re)}",
        )
    except Exception as e:
        logger.error(f"Unexpected parsing failure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the resume: {str(e)}",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def list_resumes():
    """List all previously uploaded resume records, newest first."""
    items = resume_service.repository.list_resumes(limit=50)
    return {"resumes": items, "count": len(items)}


@router.get("/{document_id}")
async def get_resume_by_id(document_id: str):
    """Retrieve a previously parsed and stored resume document by MongoDB ID."""
    doc = resume_service.repository.get_resume_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume document not found.",
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_resume_by_id(document_id: str):
    """Delete an uploaded resume document by MongoDB ID."""
    deleted = resume_service.repository.delete_resume(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume document not found or could not be deleted.",
        )
    # Cascade delete any evaluation documents for this candidate
    try:
        from app.repositories.evaluation_repository import EvaluationRepository
        EvaluationRepository().get_collection().delete_many({"candidate_id": document_id})
    except Exception as e:
        logger.warning(f"Could not cascade delete evaluations for candidate {document_id}: {str(e)}")
    return {"success": True, "message": "Resume record deleted successfully."}


@router.patch("/{document_id}/education-manual", status_code=status.HTTP_200_OK)
async def update_education_manual(document_id: str, payload: dict):
    """Manually enter Class 10 %, Class 12 %, and/or backlog count for a candidate.

    The original parsed values are preserved.  Manual values are stored with
    ``source: "manual"`` metadata.  Saving triggers automatic re-evaluation
    against every company that already has an evaluation for this candidate.

    Expected payload shape::

        {
            "class_10_percentage": 85.0,   // optional, 0–100
            "class_12_percentage": 82.5,   // optional, 0–100
            "backlogs": 0,                 // optional, integer >= 0
            "entered_by": "admin@college"  // optional identifier
        }
    """
    from datetime import datetime, timezone
    from bson import ObjectId
    from app.repositories.evaluation_repository import EvaluationRepository
    from app.repositories.company_repository import CompanyRepository
    from app.services.evaluation_engine import DeterministicEvaluationEngine

    # 1. Load the candidate document
    doc = resume_service.repository.get_resume_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume document not found.",
        )

    # 2. Validate input
    class_10 = payload.get("class_10_percentage")
    class_12 = payload.get("class_12_percentage")
    backlogs = payload.get("backlogs")
    entered_by = payload.get("entered_by", "admin")

    if class_10 is not None:
        try:
            class_10 = float(class_10)
            if not (0 <= class_10 <= 100):
                raise ValueError
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="class_10_percentage must be a number between 0 and 100.",
            )

    if class_12 is not None:
        try:
            class_12 = float(class_12)
            if not (0 <= class_12 <= 100):
                raise ValueError
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="class_12_percentage must be a number between 0 and 100.",
            )

    if backlogs is not None:
        try:
            backlogs = int(backlogs)
            if backlogs < 0:
                raise ValueError
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="backlogs must be an integer >= 0.",
            )

    if class_10 is None and class_12 is None and backlogs is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of class_10_percentage, class_12_percentage, or backlogs is required.",
        )

    # 3. Build $set update — preserve the original parsed value
    now_iso = datetime.now(timezone.utc).isoformat()
    update_fields = {}

    education = doc.get("education", []) or []
    # Find the first college-level record to attach manual data to
    target_idx = 0
    for idx, edu in enumerate(education):
        deg = (edu.get("degree") or "").lower()
        is_school = any(k in deg for k in [
            "class x", "10th", "secondary", "ssc", "matriculation",
            "class xii", "12th", "higher secondary", "hsc", "intermediate",
        ])
        if not is_school:
            target_idx = idx
            break

    prefix = f"education.{target_idx}"

    if class_10 is not None:
        update_fields[f"{prefix}.class_10_percentage"] = f"{class_10}%"
        update_fields[f"{prefix}.class_10_manual"] = {
            "value": f"{class_10}%",
            "source": "manual",
            "entered_by": entered_by,
            "entered_at": now_iso,
        }

    if class_12 is not None:
        update_fields[f"{prefix}.class_12_percentage"] = f"{class_12}%"
        update_fields[f"{prefix}.class_12_manual"] = {
            "value": f"{class_12}%",
            "source": "manual",
            "entered_by": entered_by,
            "entered_at": now_iso,
        }

    if backlogs is not None:
        update_fields[f"{prefix}.backlogs"] = backlogs
        update_fields[f"{prefix}.backlogs_manual"] = {
            "value": backlogs,
            "source": "manual",
            "entered_by": entered_by,
            "entered_at": now_iso,
        }

    # 4. Persist to MongoDB
    try:
        coll = resume_service.repository.get_collection()
        result = coll.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_fields},
        )
        if result.modified_count == 0 and result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume document not found during update.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update manual education data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed: {str(e)}",
        )

    # 5. Re-evaluate against all companies that have existing evaluations
    eval_repo = EvaluationRepository()
    company_repo = CompanyRepository()
    updated_doc = resume_service.repository.get_resume_by_id(document_id)
    re_evaluated = []

    try:
        eval_coll = eval_repo.get_collection()
        existing_evals = list(eval_coll.find({"candidate_id": document_id}))
        seen_company_ids = set()
        for ev in existing_evals:
            cid = ev.get("company_id")
            if cid and cid not in seen_company_ids:
                seen_company_ids.add(cid)
                company_doc = company_repo.get_company_by_id(cid)
                if company_doc and updated_doc:
                    new_eval = DeterministicEvaluationEngine.evaluate(
                        candidate=updated_doc,
                        company_req=company_doc,
                        candidate_id=document_id,
                        company_id=cid,
                    )
                    eval_id = eval_repo.save_evaluation(new_eval.model_dump())
                    re_evaluated.append(eval_id)
    except Exception as e:
        logger.warning(f"Auto re-evaluation after manual entry failed: {str(e)}")

    return {
        "success": True,
        "message": "Manual education data saved successfully.",
        "updated_fields": list(update_fields.keys()),
        "re_evaluated_count": len(re_evaluated),
    }
