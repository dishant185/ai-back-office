"""MongoDB index initialization for multi-tenant isolation and query performance."""
from __future__ import annotations

import logging
from pymongo import ASCENDING, DESCENDING

from app.db.database import (
    get_accounts_collection,
    get_users_collection,
    get_datasets_collection,
    get_dataset_schemas_collection,
    get_dataset_knowledge_collection,
    get_conversations_collection,
    get_messages_collection,
    get_reports_collection,
    get_audit_logs_collection,
    get_mappings_collection,
)

logger = logging.getLogger(__name__)


def _safe_create_index(col, keys, **kwargs):
    try:
        col.create_index(keys, **kwargs)
    except Exception:
        pass


def init_indexes() -> None:
    """Create all required MongoDB indexes."""
    try:
        # Accounts
        _safe_create_index(get_accounts_collection(), [("account_id", ASCENDING)], unique=True)

        # Users
        users = get_users_collection()
        _safe_create_index(users, [("email", ASCENDING)], unique=True)
        _safe_create_index(users, [("account_id", ASCENDING)])
        _safe_create_index(users, [("id", ASCENDING)])

        # Datasets
        datasets = get_datasets_collection()
        _safe_create_index(datasets, [("dataset_id", ASCENDING)])
        _safe_create_index(datasets, [("upload_id", ASCENDING)])
        _safe_create_index(datasets, [("account_id", ASCENDING)])
        _safe_create_index(datasets, [("account_id", ASCENDING), ("created_at", DESCENDING)])
        _safe_create_index(datasets, [("user_id", ASCENDING)])

        # Schemas
        schemas = get_dataset_schemas_collection()
        _safe_create_index(schemas, [("dataset_id", ASCENDING)])
        _safe_create_index(schemas, [("account_id", ASCENDING)])

        # Dataset Knowledge
        knowledge = get_dataset_knowledge_collection()
        _safe_create_index(knowledge, [("dataset_id", ASCENDING)])
        _safe_create_index(knowledge, [("account_id", ASCENDING)])

        # Conversations
        conversations = get_conversations_collection()
        _safe_create_index(conversations, [("conversation_id", ASCENDING)])
        _safe_create_index(conversations, [("session_id", ASCENDING)])
        _safe_create_index(conversations, [("account_id", ASCENDING)])
        _safe_create_index(conversations, [("user_id", ASCENDING)])
        _safe_create_index(conversations, [("dataset_id", ASCENDING)])

        # Messages
        messages = get_messages_collection()
        _safe_create_index(messages, [("conversation_id", ASCENDING), ("created_at", ASCENDING)])
        _safe_create_index(messages, [("account_id", ASCENDING)])

        # Reports
        reports = get_reports_collection()
        _safe_create_index(reports, [("report_id", ASCENDING)])
        _safe_create_index(reports, [("account_id", ASCENDING)])
        _safe_create_index(reports, [("dataset_id", ASCENDING)])

        # Dataset Versions
        from app.db.database import (
            get_dataset_versions_collection,
            get_report_versions_collection,
            get_report_evidence_collection,
            get_ai_validation_logs_collection,
            get_ai_generation_logs_collection,
            get_report_ai_summaries_collection,
        )
        ds_versions = get_dataset_versions_collection()
        _safe_create_index(ds_versions, [("dataset_id", ASCENDING), ("dataset_version", ASCENDING)])
        _safe_create_index(ds_versions, [("account_id", ASCENDING)])

        # Report Versions
        rep_versions = get_report_versions_collection()
        _safe_create_index(rep_versions, [("report_id", ASCENDING), ("report_version", ASCENDING)])
        _safe_create_index(rep_versions, [("account_id", ASCENDING)])

        # Report Evidence
        rep_ev = get_report_evidence_collection()
        _safe_create_index(rep_ev, [("report_id", ASCENDING)])
        _safe_create_index(rep_ev, [("account_id", ASCENDING)])

        # AI Summaries
        ai_sums = get_report_ai_summaries_collection()
        _safe_create_index(ai_sums, [("report_id", ASCENDING), ("filters_hash", ASCENDING)])
        _safe_create_index(ai_sums, [("account_id", ASCENDING)])

        # Validation & Generation Logs
        _safe_create_index(get_ai_validation_logs_collection(), [("account_id", ASCENDING), ("created_at", DESCENDING)])
        _safe_create_index(get_ai_generation_logs_collection(), [("account_id", ASCENDING), ("created_at", DESCENDING)])

        # Compound Tenant / Account indexes across primary collections
        for col in [datasets, schemas, knowledge, conversations, messages, reports]:
            _safe_create_index(col, [("tenant_id", ASCENDING), ("account_id", ASCENDING)])

        logger.info("MongoDB multi-tenant indexes verified successfully.")
    except Exception as exc:
        logger.warning("Failed to initialize some MongoDB indexes: %s", exc)

        # Mappings (legacy)
        mappings = get_mappings_collection()
        mappings.create_index([("upload_id", ASCENDING)])
        mappings.create_index([("user_id", ASCENDING)])

        logger.info("MongoDB indexes verified successfully.")
    except Exception as exc:
        logger.warning("Failed to initialize some MongoDB indexes: %s", exc)


def init_db_indexes() -> None:
    """Legacy alias."""
    init_indexes()
