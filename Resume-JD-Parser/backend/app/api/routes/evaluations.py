"""API routes for Deterministic Candidate Evaluation."""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.evaluation_schema import (
    EvaluateRequestSchema,
    EvaluationCanonicalSchema,
)
from app.repositories.company_repository import CompanyRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.services.evaluation_engine import DeterministicEvaluationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

company_repo = CompanyRepository()
resume_repo = ResumeRepository()
eval_repo = EvaluationRepository()


@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_candidates(payload: EvaluateRequestSchema):
    """Run deterministic Python evaluation for candidates against a company requirement.

    STRICT: Pure deterministic Python rules only. No AI, LLMs, or OpenAI APIs are invoked.
    If payload.candidate_id is provided, evaluates that candidate.
    If payload.candidate_id is omitted or null, evaluates all candidates in the system.
    """
    company_id = payload.company_id
    company_doc = company_repo.get_company_by_id(company_id)
    if not company_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company recruitment requirement with ID '{company_id}' not found.",
        )

    # Single Candidate Evaluation
    if payload.candidate_id:
        cand_doc = resume_repo.get_resume_by_id(payload.candidate_id)
        if not cand_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate resume with ID '{payload.candidate_id}' not found.",
            )

        evaluation_obj = DeterministicEvaluationEngine.evaluate(
            candidate=cand_doc,
            company_req=company_doc,
            candidate_id=payload.candidate_id,
            company_id=company_id,
        )
        eval_dict = evaluation_obj.model_dump()
        eval_id = eval_repo.save_evaluation(eval_dict)
        saved_eval = eval_repo.get_evaluation_by_id(eval_id)

        return {
            "success": True,
            "message": "Candidate evaluated deterministically.",
            "evaluation_id": eval_id,
            "data": saved_eval,
        }

    # Batch Candidate Evaluation (All Candidates)
    try:
        # Retrieve all candidates from database
        coll = resume_repo.get_collection()
        all_candidates = list(coll.find())
        active_ids = set()

        for cand_doc in all_candidates:
            cand_id = str(cand_doc.get("_id", ""))
            active_ids.add(cand_id)
            evaluation_obj = DeterministicEvaluationEngine.evaluate(
                candidate=cand_doc,
                company_req=company_doc,
                candidate_id=cand_id,
                company_id=company_id,
            )
            eval_dict = evaluation_obj.model_dump()
            eval_repo.save_evaluation(eval_dict)

        # Cleanup orphaned evaluations for candidates no longer in database
        if active_ids:
            try:
                eval_coll = eval_repo.get_collection()
                all_evals = list(eval_coll.find({"company_id": company_id}))
                for ev in all_evals:
                    if ev.get("candidate_id") not in active_ids:
                        eval_coll.delete_one({"_id": ev["_id"]})
            except Exception as clean_err:
                logger.warning(f"Failed to clean orphaned evaluations: {str(clean_err)}")

        # Fetch updated deduplicated evaluations for this company
        evaluations_list = eval_repo.list_evaluations_for_company(company_id)

        return {
            "success": True,
            "message": f"Successfully evaluated {len(evaluations_list)} candidate(s) deterministically.",
            "count": len(evaluations_list),
            "evaluations": evaluations_list,
        }
    except Exception as e:
        logger.error(f"Error evaluating candidates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


@router.get("/company/{company_id}", status_code=status.HTTP_200_OK)
async def list_evaluations_for_company(company_id: str):
    """Retrieve all evaluation results for a company requirement."""
    # Verify company exists
    company_doc = company_repo.get_company_by_id(company_id)
    if not company_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company recruitment requirement with ID '{company_id}' not found.",
        )
    items = eval_repo.list_evaluations_for_company(company_id)
    return {
        "company_id": company_id,
        "company_name": company_doc.get("company", {}).get("name"),
        "job_role": company_doc.get("company", {}).get("job_role"),
        "evaluations": items,
        "count": len(items),
    }


@router.get("/{evaluation_id}", status_code=status.HTTP_200_OK)
async def get_evaluation_by_id(evaluation_id: str):
    """Retrieve a single evaluation result by its MongoDB ID."""
    doc = eval_repo.get_evaluation_by_id(evaluation_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation document not found.",
        )
    return doc
