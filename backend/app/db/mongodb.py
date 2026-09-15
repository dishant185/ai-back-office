from __future__ import annotations

import logging
from typing import Any
from pymongo import ASCENDING, MongoClient
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
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )
            # Test connection
            _mongo_client.admin.command("ping")
            logger.info("Connected to MongoDB successfully at %s", settings.mongodb_url)
        except Exception as e:
            logger.warning("Failed to connect to MongoDB at %s: %s", settings.mongodb_url, e)
            _mongo_client = MongoClient(settings.mongodb_url)
    return _mongo_client


def get_database() -> Database[dict[str, Any]]:
    client = get_mongo_client()
    return client[settings.mongodb_db_name]


def get_users_collection() -> Collection[dict[str, Any]]:
    return get_database()["users"]


def get_uploads_collection() -> Collection[dict[str, Any]]:
    return get_database()["uploads"]


def get_mappings_collection() -> Collection[dict[str, Any]]:
    return get_database()["mappings"]


def get_reports_collection() -> Collection[dict[str, Any]]:
    return get_database()["reports"]


def init_db_indexes() -> None:
    """Initialize critical performance & uniqueness indexes."""
    try:
        users = get_users_collection()
        users.create_index([("email", ASCENDING)], unique=True)
        users.create_index([("id", ASCENDING)], unique=True)

        uploads = get_uploads_collection()
        uploads.create_index([("upload_id", ASCENDING)], unique=True)
        uploads.create_index([("user_id", ASCENDING)])
        uploads.create_index([("created_at", ASCENDING)])

        mappings = get_mappings_collection()
        mappings.create_index([("upload_id", ASCENDING)])
        mappings.create_index([("user_id", ASCENDING)])

        reports = get_reports_collection()
        reports.create_index([("report_id", ASCENDING)], unique=True)
        reports.create_index([("user_id", ASCENDING)])
        reports.create_index([("dataset_id", ASCENDING)])
        reports.create_index([("generated_at", ASCENDING)])

        logger.info("MongoDB collections and indexes initialized successfully in '%s'.", settings.mongodb_db_name)
    except Exception as e:
        logger.warning("Could not initialize MongoDB indexes: %s", e)
