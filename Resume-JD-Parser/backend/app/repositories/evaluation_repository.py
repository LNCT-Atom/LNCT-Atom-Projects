"""MongoDB persistence repository for Candidate Evaluations."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

from app.core.config import settings

logger = logging.getLogger(__name__)


class EvaluationRepositoryError(Exception):
    """Custom exception for evaluation repository operations."""
    pass


class EvaluationRepository:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or settings.MONGODB_URI
        self.db_name = db_name or settings.MONGODB_DATABASE
        self._client: Optional[MongoClient] = None
        self._collection: Optional[Collection] = None

    def get_collection(self) -> Collection:
        """Use centralized database connection for the evaluations collection."""
        from app.core.database import get_collection as get_db_collection
        return get_db_collection(settings.MONGODB_EVALUATION_COLLECTION)

    def save_evaluation(self, eval_data: Dict[str, Any]) -> str:
        """Upsert evaluation document for (company_id, candidate_id)."""
        try:
            coll = self.get_collection()
            doc_to_save = dict(eval_data)
            now_iso = datetime.now(timezone.utc).isoformat()
            doc_to_save["updated_at"] = now_iso

            company_id = doc_to_save.get("company_id")
            candidate_id = doc_to_save.get("candidate_id")
            candidate_email = doc_to_save.get("candidate_email")

            # Check if evaluation already exists for this pair (by email or candidate_id)
            existing = None
            if candidate_email:
                import re
                existing = coll.find_one({
                    "company_id": company_id,
                    "candidate_email": {"$regex": f"^{re.escape(candidate_email.strip())}$", "$options": "i"}
                })
            if not existing:
                existing = coll.find_one({"company_id": company_id, "candidate_id": candidate_id})

            if existing:
                eval_id = str(existing["_id"])
                if "_id" in doc_to_save:
                    del doc_to_save["_id"]
                if "id" in doc_to_save:
                    del doc_to_save["id"]
                coll.update_one({"_id": existing["_id"]}, {"$set": doc_to_save})
                return eval_id
            else:
                doc_to_save["created_at"] = now_iso
                res = coll.insert_one(doc_to_save)
                return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to persist evaluation: {str(e)}")
            raise EvaluationRepositoryError(f"Persistence error: {str(e)}")

    def get_evaluation_by_id(self, eval_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evaluation document by MongoDB ID."""
        try:
            coll = self.get_collection()
            doc = coll.find_one({"_id": ObjectId(eval_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Error fetching evaluation {eval_id}: {str(e)}")
            return None

    def list_evaluations_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        """List all candidate evaluations for a specific company requirement, deduplicated by candidate."""
        try:
            coll = self.get_collection()
            cursor = coll.find({"company_id": company_id}).sort([("updated_at", -1), ("created_at", -1)])
            items = []
            seen_candidates = set()
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                doc["_id"] = str(doc["_id"])
                cand_key = (doc.get("candidate_id") or doc.get("candidate_email") or doc.get("candidate_name") or "").strip().lower()
                if cand_key:
                    if cand_key in seen_candidates:
                        continue
                    seen_candidates.add(cand_key)
                items.append(doc)
            return items
        except Exception as e:
            logger.error(f"Error listing evaluations for company {company_id}: {str(e)}")
            return []

    def delete_evaluations_by_company(self, company_id: str) -> int:
        """Delete all evaluations associated with a company requirement."""
        try:
            coll = self.get_collection()
            res = coll.delete_many({"company_id": company_id})
            return res.deleted_count
        except Exception as e:
            logger.error(f"Error deleting evaluations for company {company_id}: {str(e)}")
            return 0
