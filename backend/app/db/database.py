"""MongoDB database client and collection providers for AI Back-Office Copilot."""
from __future__ import annotations

import logging
from typing import Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.config import settings

logger = logging.getLogger(__name__)

_mongo_client: MongoClient[dict[str, Any]] | None = None


def get_mongo_client() -> MongoClient[dict[str, Any]]:
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
            )
            _mongo_client.admin.command("ping")
            logger.info("Connected to MongoDB at %s", settings.mongodb_url)
        except Exception as err:
            logger.warning("Failed to connect to MongoDB at %s: %s", settings.mongodb_url, err)
            _mongo_client = MongoClient(settings.mongodb_url)
    return _mongo_client


def check_mongo_health() -> dict[str, Any]:
    """Test active MongoDB connectivity."""
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        return {
            "status": "healthy",
            "connected": True,
            "database": settings.mongodb_db_name,
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "connected": False,
            "database": settings.mongodb_db_name,
            "error": str(exc),
        }


def get_database_optional() -> Database[dict[str, Any]] | None:
    """Return MongoDB Database instance if verified connected, else None."""
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        return client[settings.mongodb_db_name]
    except Exception:
        return None


def get_database() -> Database[dict[str, Any]]:
    client = get_mongo_client()
    return client[settings.mongodb_db_name]


def get_accounts_collection() -> Collection[dict[str, Any]]:
    return get_database()["accounts"]


def get_users_collection() -> Collection[dict[str, Any]]:
    return get_database()["users"]


def get_datasets_collection() -> Collection[dict[str, Any]]:
    return get_database()["datasets"]


def get_dataset_schemas_collection() -> Collection[dict[str, Any]]:
    return get_database()["dataset_schemas"]


def get_dataset_knowledge_collection() -> Collection[dict[str, Any]]:
    return get_database()["dataset_knowledge"]


def get_conversations_collection() -> Collection[dict[str, Any]]:
    return get_database()["conversations"]


def get_messages_collection() -> Collection[dict[str, Any]]:
    return get_database()["messages"]


def get_reports_collection() -> Collection[dict[str, Any]]:
    return get_database()["reports"]


def get_analytics_jobs_collection() -> Collection[dict[str, Any]]:
    return get_database()["analytics_jobs"]


def get_audit_logs_collection() -> Collection[dict[str, Any]]:
    return get_database()["audit_logs"]


# Legacy alias
def get_uploads_collection() -> Collection[dict[str, Any]]:
    return get_datasets_collection()


def get_mappings_collection() -> Collection[dict[str, Any]]:
    return get_database()["mappings"]


def get_report_summaries_collection() -> Collection[dict[str, Any]]:
    return get_database()["report_summaries"]


def get_report_ai_summaries_collection() -> Collection[dict[str, Any]]:
    return get_database()["report_ai_summaries"]


def get_dataset_versions_collection() -> Collection[dict[str, Any]]:
    return get_database()["dataset_versions"]


def get_report_versions_collection() -> Collection[dict[str, Any]]:
    return get_database()["report_versions"]


def get_report_evidence_collection() -> Collection[dict[str, Any]]:
    return get_database()["report_evidence"]


def get_ai_validation_logs_collection() -> Collection[dict[str, Any]]:
    return get_database()["ai_validation_logs"]


def get_ai_generation_logs_collection() -> Collection[dict[str, Any]]:
    return get_database()["ai_generation_logs"]

