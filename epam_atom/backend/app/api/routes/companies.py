"""API routes for Company Recruitment Requirements."""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.company_schema import (
    CompanyRequirementCreateSchema,
    CompanyRequirementSchema,
)
from app.repositories.company_repository import (
    CompanyRepository,
    CompanyRepositoryError,
)
from app.repositories.evaluation_repository import EvaluationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["Companies"])
company_repo = CompanyRepository()
eval_repo = EvaluationRepository()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_company_requirement(payload: CompanyRequirementCreateSchema):
    """Create a new company recruitment requirement.

    Validates incoming data against CompanyRequirementCreateSchema and persists to MongoDB.
    """
    try:
        data_dict = payload.model_dump()
        doc_id = company_repo.insert_company(data_dict)
        saved_doc = company_repo.get_company_by_id(doc_id)
        return {
            "success": True,
            "message": "Company recruitment requirement created successfully.",
            "company_id": doc_id,
            "data": saved_doc,
        }
    except CompanyRepositoryError as cre:
        logger.error(f"Error persisting company requirement: {str(cre)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company requirement: {str(cre)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error creating company requirement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def list_company_requirements(
    search: Optional[str] = Query(None, description="Search companies by name, role, or location"),
    limit: int = Query(100, ge=1, le=500),
):
    """List submitted company requirements with search and filter capabilities."""
    items = company_repo.list_companies(search=search, limit=limit)
    return {"companies": items, "count": len(items)}


@router.get("/{company_id}", status_code=status.HTTP_200_OK)
async def get_company_requirement(company_id: str):
    """Fetch single company requirement by its MongoDB ID."""
    doc = company_repo.get_company_by_id(company_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company recruitment requirement not found.",
        )
    return doc


@router.put("/{company_id}", status_code=status.HTTP_200_OK)
async def update_company_requirement(
    company_id: str, payload: CompanyRequirementCreateSchema
):
    """Update an existing company recruitment requirement."""
    existing = company_repo.get_company_by_id(company_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company recruitment requirement not found.",
        )
    try:
        updated = company_repo.update_company(company_id, payload.model_dump())
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update requirement.",
            )
        fresh_doc = company_repo.get_company_by_id(company_id)
        return {
            "success": True,
            "message": "Company recruitment requirement updated successfully.",
            "data": fresh_doc,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company requirement {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}",
        )


@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company_requirement(company_id: str):
    """Delete a company requirement and any associated candidate evaluations."""
    deleted = company_repo.delete_company(company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company recruitment requirement not found or could not be deleted.",
        )
    # Clean up associated candidate evaluations
    eval_repo.delete_evaluations_by_company(company_id)
    return {
        "success": True,
        "message": "Company recruitment requirement deleted successfully.",
    }
