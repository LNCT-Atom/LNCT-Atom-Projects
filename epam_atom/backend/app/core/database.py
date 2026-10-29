# Centralized MongoDB connection handling
"""Database utilities for MongoDB connection.

All repository classes should import ``get_collection`` from this module
instead of instantiating their own ``MongoClient``.  This guarantees a
single client per process, consistent configuration, and a single place to
adjust connection logic (e.g. TLS, time‑outs, fallback to ``mongomock``).
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module‑level cache for the client instance
_client: Optional[MongoClient] = None


def _create_client() -> MongoClient:
    """Create a new ``MongoClient`` according to environment settings.

    The function mirrors the logic previously duplicated in the individual
    repositories: it chooses a timeout based on whether the URI points to an
    Atlas cluster, loads the CA bundle via ``certifi`` when required, and
    falls back to an in‑memory ``mongomock`` client if the real connection
    cannot be established.
    """
    # Resolve placeholder credentials – if present, fall back to a local DB.
    effective_uri = settings.MONGODB_URI
    if "<db_password>" in effective_uri or "<password>" in effective_uri:
        logger.warning(
            "MongoDB URI contains placeholder credentials. Using local MongoDB "
            "mongodb://localhost:27017."
        )
        effective_uri = "mongodb://localhost:27017"

    is_atlas = "mongodb+srv://" in effective_uri or "mongodb.net" in effective_uri
    timeout_ms = 10000 if is_atlas else 3000

    client_kwargs = {
        "serverSelectionTimeoutMS": timeout_ms,
        "connectTimeoutMS": timeout_ms,
        "socketTimeoutMS": timeout_ms,
    }

    # Atlas requires a trusted CA bundle.
    try:
        import certifi

        tls_ca = certifi.where()
    except Exception:
        tls_ca = None
    if tls_ca and is_atlas:
        client_kwargs["tlsCAFile"] = tls_ca

    try:
        client = MongoClient(effective_uri, **client_kwargs)
        # Verify connection early.
        client.admin.command("ping")
        uri_display = (
            effective_uri[:40] + "..." if len(effective_uri) > 40 else effective_uri
        )
        logger.info(f"[MONGODB] Connected successfully to: {uri_display}")
        return client
    except Exception as primary_err:
        # Real MongoDB unreachable – fall back to mongomock.
        try:
            import mongomock

            logger.warning(
                "[MONGODB] Real MongoDB connection failed; using in‑memory mongomock."
            )
            return mongomock.MongoClient()
        except Exception as mongomock_err:
            logger.error(
                f"[MONGODB] Both real connection and mongomock fallback failed: "
                f"{mongomock_err}"
            )
            raise RuntimeError(
                f"Database connection error: {primary_err}; mongomock error: {mongomock_err}"
            ) from primary_err


def get_client() -> MongoClient:
    """Return a cached ``MongoClient`` instance, creating it on first use."""
    global _client
    if _client is None:
        _client = _create_client()
    return _client


def get_collection(collection_name: str) -> Collection:
    """Convenient helper returning the requested collection.

    ``collection_name`` should match the constant defined in ``settings`` (for
    example ``settings.MONGODB_COLLECTION``).  The underlying database name is
    taken from ``settings.MONGODB_DATABASE``.
    """
    client = get_client()
    db = client[settings.MONGODB_DATABASE]
    collection = db[collection_name]
    # Ensure indexes used by the application exist.
    if collection_name == settings.MONGODB_COLLECTION:
        collection.create_index("metadata.file_hash")
        collection.create_index("created_at")
    return collection
