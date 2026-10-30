"""MongoDB persistence repository for resumes using PyMongo."""
import logging
from typing import List
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ResumeRepositoryError(Exception):
    """Custom exception for database errors."""
    pass


class ResumeRepository:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or settings.MONGODB_URI
        self.db_name = db_name or settings.MONGODB_DATABASE
        self._client: Optional[MongoClient] = None
        self._db = None
        self._collection: Optional[Collection] = None

    def get_collection(self) -> Collection:
        """Use centralized database connection to obtain the resumes collection."""
        # Import locally to avoid circular imports
        from app.core.database import get_collection as get_db_collection
        return get_db_collection(settings.MONGODB_COLLECTION)

    def find_by_file_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Look for an existing resume by its SHA-256 file content hash."""
        try:
            coll = self.get_collection()
            doc = coll.find_one({"metadata.file_hash": file_hash})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except (PyMongoError, ResumeRepositoryError, Exception) as e:
            logger.warning(f"Error checking for duplicate resume: {str(e)}")
            return None

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look for an existing resume by candidate email."""
        if not email:
            return None
        import re
        try:
            coll = self.get_collection()
            doc = coll.find_one({"profile.email": {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"}})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except (PyMongoError, ResumeRepositoryError, Exception) as e:
            logger.warning(f"Error checking resume by email: {str(e)}")
            return None

    def upsert_resume(self, resume_data: Dict[str, Any]) -> str:
        """Insert or replace resume if matching candidate email or file hash already exists."""
        try:
            coll = self.get_collection()
            doc_to_save = dict(resume_data)
            now = datetime.now(timezone.utc)
            doc_to_save["updated_at"] = now

            email = doc_to_save.get("profile", {}).get("email")
            file_hash = doc_to_save.get("metadata", {}).get("file_hash")

            existing = None
            if email:
                import re
                existing = coll.find_one({"profile.email": {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"}})
            if not existing and file_hash:
                existing = coll.find_one({"metadata.file_hash": file_hash})

            if existing:
                doc_id = str(existing["_id"])
                doc_to_save["created_at"] = existing.get("created_at", now)
                coll.replace_one({"_id": existing["_id"]}, doc_to_save)
                logger.info(f"[MONGODB_UPSERT] Replaced existing resume document with ID={doc_id}")
                return doc_id
            else:
                doc_to_save["created_at"] = now
                result = coll.insert_one(doc_to_save)
                if not result.acknowledged or not result.inserted_id:
                    raise ResumeRepositoryError("MongoDB write was not acknowledged by the server.")
                return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Failed to persist resume document into MongoDB: {str(e)}")
            raise ResumeRepositoryError(f"Database persistence failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error persisting resume: {str(e)}")
            raise ResumeRepositoryError(f"Unexpected database error: {str(e)}")

    def insert_resume(self, resume_data: Dict[str, Any]) -> str:
        """Insert one validated resume document into MongoDB and return the generated document ID."""
        return self.upsert_resume(resume_data)

    def get_resume_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored resume by MongoDB ObjectID."""
        from bson import ObjectId
        try:
            coll = self.get_collection()
            doc = coll.find_one({"_id": ObjectId(document_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Error fetching resume document {document_id}: {str(e)}")
            return None

    def list_resumes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve a list of uploaded resume records, newest first."""
        try:
            coll = self.get_collection()
            cursor = coll.find().sort("created_at", -1).limit(limit)
            items = []
            for doc in cursor:
                doc_id = str(doc.get("_id", ""))
                metadata = doc.get("metadata", {}) or {}
                profile = doc.get("profile", {}) or {}
                tech_skills = doc.get("technical_skills", {}) or {}

                created_at = doc.get("created_at")
                if isinstance(created_at, datetime):
                    created_at_str = created_at.isoformat()
                else:
                    created_at_str = str(created_at or metadata.get("parsed_at") or "")

                skills_count = len(tech_skills.get("technologies", []))
                if skills_count == 0:
                    skills_count = (
                        len(tech_skills.get("programming_languages", []))
                        + len(tech_skills.get("frameworks", []))
                        + len(tech_skills.get("databases", []))
                        + len(tech_skills.get("tools", []))
                    )

                items.append({
                    "id": doc_id,
                    "filename": metadata.get("file_name") or "resume.pdf",
                    "created_at": created_at_str,
                    "status": metadata.get("status", "completed"),
                    "candidate_name": profile.get("full_name"),
                    "candidate_email": profile.get("email"),
                    "candidate_phone": profile.get("phone"),
                    "skills_count": skills_count,
                    "education_count": len(doc.get("education", []) or []),
                    "projects_count": len(doc.get("projects", []) or []),
                    "is_scanned_pdf": metadata.get("is_scanned_pdf", False),
                })
            return items
        except Exception as e:
            logger.error(f"Error listing uploaded resumes: {str(e)}")
            return []

    def delete_resume(self, document_id: str) -> bool:
        """Delete an uploaded resume by its MongoDB ObjectID and cascade delete related evaluations."""
        import re
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            coll = self.get_collection()
            try:
                oid = ObjectId(document_id)
            except (InvalidId, TypeError):
                logger.warning(f"Invalid document_id format for deletion: {document_id}")
                return False

            # Check if document exists and capture candidate identifiers for cascade cleanup
            existing_doc = coll.find_one({"_id": oid})
            if not existing_doc:
                return False

            candidate_email = existing_doc.get("profile", {}).get("email")

            # Delete the resume document
            result = coll.delete_one({"_id": oid})
            deleted = result.deleted_count > 0

            if deleted:
                # Cascade delete related evaluations
                try:
                    from app.repositories.evaluation_repository import EvaluationRepository
                    eval_coll = EvaluationRepository().get_collection()
                    eval_or_clauses = [
                        {"candidate_id": str(document_id)},
                        {"candidate_id": oid},
                    ]
                    if candidate_email and candidate_email.strip():
                        eval_or_clauses.append({
                            "candidate_email": {"$regex": f"^{re.escape(candidate_email.strip())}$", "$options": "i"}
                        })
                    eval_coll.delete_many({"$or": eval_or_clauses})
                except Exception as e:
                    logger.warning(f"Could not cascade delete evaluations for candidate {document_id}: {str(e)}")

            return deleted
        except Exception as e:
            logger.error(f"Error deleting resume {document_id}: {str(e)}")
            return False

