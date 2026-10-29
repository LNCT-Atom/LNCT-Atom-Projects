"""MongoDB persistence repository for Company Recruitment Requirements."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from bson import ObjectId

from app.core.config import settings

logger = logging.getLogger(__name__)


class CompanyRepositoryError(Exception):
    """Custom exception for company repository database operations."""
    pass


class CompanyRepository:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or settings.MONGODB_URI
        self.db_name = db_name or settings.MONGODB_DATABASE
        self._client: Optional[MongoClient] = None
        self._collection: Optional[Collection] = None

    def get_collection(self) -> Collection:
        """Use centralized database connection for the companies collection."""
        from app.core.database import get_collection as get_db_collection
        return get_db_collection(settings.MONGODB_COMPANY_COLLECTION)

    def insert_company(self, company_data: Dict[str, Any]) -> str:
        """Insert one validated company recruitment requirement into MongoDB."""
        try:
            coll = self.get_collection()
            doc_to_save = dict(company_data)
            now_iso = datetime.now(timezone.utc).isoformat()
            doc_to_save["created_at"] = now_iso
            doc_to_save["updated_at"] = now_iso

            result = coll.insert_one(doc_to_save)
            if not result.acknowledged or not result.inserted_id:
                raise CompanyRepositoryError("MongoDB write was not acknowledged.")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to persist company requirement: {str(e)}")
            raise CompanyRepositoryError(f"Persistence error: {str(e)}")

    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored company requirement by MongoDB ObjectID."""
        try:
            coll = self.get_collection()
            doc = coll.find_one({"_id": ObjectId(company_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {str(e)}")
            return None

    def list_companies(self, search: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List company requirements, newest first, with optional search filter."""
        try:
            coll = self.get_collection()
            query_filter = {}
            if search and search.strip():
                regex = {"$regex": search.strip(), "$options": "i"}
                query_filter = {
                    "$or": [
                        {"company.name": regex},
                        {"company.job_role": regex},
                        {"company.location": regex},
                        {"company.job_type": regex},
                    ]
                }
            cursor = coll.find(query_filter).sort("created_at", -1).limit(limit)
            items = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                doc["_id"] = str(doc["_id"])
                items.append(doc)
            return items
        except Exception as e:
            logger.error(f"Error listing companies: {str(e)}")
            return []

    def update_company(self, company_id: str, company_data: Dict[str, Any]) -> bool:
        """Update an existing company requirement."""
        try:
            coll = self.get_collection()
            doc_to_update = dict(company_data)
            doc_to_update["updated_at"] = datetime.now(timezone.utc).isoformat()
            if "_id" in doc_to_update:
                del doc_to_update["_id"]
            if "id" in doc_to_update:
                del doc_to_update["id"]

            res = coll.update_one({"_id": ObjectId(company_id)}, {"$set": doc_to_update})
            return res.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating company {company_id}: {str(e)}")
            raise CompanyRepositoryError(f"Update error: {str(e)}")

    def delete_company(self, company_id: str) -> bool:
        """Delete a company requirement by MongoDB ObjectID."""
        try:
            coll = self.get_collection()
            res = coll.delete_one({"_id": ObjectId(company_id)})
            return res.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting company {company_id}: {str(e)}")
            return False
