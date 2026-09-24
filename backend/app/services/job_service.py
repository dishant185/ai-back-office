"""Processing job system and state machine for Novera Enterprise Multi-Tenant Platform."""
from __future__ import annotations

import datetime
import logging
from typing import Any
import uuid

from app.db.database import get_processing_jobs_collection

logger = logging.getLogger(__name__)

# Job States
JOB_STATE_QUEUED = "QUEUED"
JOB_STATE_PROCESSING = "PROCESSING"
JOB_STATE_COMPLETED = "COMPLETED"
JOB_STATE_FAILED = "FAILED"
JOB_STATE_CANCELLED = "CANCELLED"

# Pipeline Stages
STAGE_UPLOADED = "UPLOADED"
STAGE_VALIDATING = "VALIDATING"
STAGE_PROFILING = "PROFILING"
STAGE_MAPPING = "MAPPING"
STAGE_QUALITY = "QUALITY"
STAGE_ANALYZING = "ANALYZING"
STAGE_KNOWLEDGE = "KNOWLEDGE"
STAGE_READY = "READY"

ALLOWED_STAGES = [
    STAGE_UPLOADED,
    STAGE_VALIDATING,
    STAGE_PROFILING,
    STAGE_MAPPING,
    STAGE_QUALITY,
    STAGE_ANALYZING,
    STAGE_KNOWLEDGE,
    STAGE_READY,
]


def create_processing_job(
    account_id: str,
    user_id: str,
    dataset_id: str,
    dataset_version: int = 1,
    job_type: str = "DATASET_PROCESSING",
    workspace_id: str = "default",
) -> dict[str, Any]:
    """Create a persistent processing job in QUEUED state."""
    job_id = f"job_{uuid.uuid4().hex[:14]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    doc: dict[str, Any] = {
        "job_id": job_id,
        "account_id": account_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "job_type": job_type,
        "status": JOB_STATE_QUEUED,
        "current_stage": STAGE_UPLOADED,
        "progress": 0,
        "attempt_count": 1,
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "heartbeat_at": now,
        "failure_code": None,
        "safe_failure_message": None,
    }

    col = get_processing_jobs_collection()
    col.insert_one(doc)
    logger.info("Created processing job %s for account %s (dataset: %s)", job_id, account_id, dataset_id)
    return doc


def update_job_stage(
    job_id: str,
    account_id: str,
    stage: str,
    progress: int,
) -> bool:
    """Safely transition the job through its processing pipeline."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    col = get_processing_jobs_collection()

    update_doc: dict[str, Any] = {
        "status": JOB_STATE_PROCESSING,
        "current_stage": stage,
        "progress": max(0, min(progress, 100)),
        "heartbeat_at": now,
        "updated_at": now,
    }

    res = col.update_one(
        {"job_id": job_id, "account_id": account_id},
        {
            "$set": update_doc,
            "$setOnInsert": {"started_at": now},
        },
    )
    return res.matched_count > 0


def complete_job(
    job_id: str,
    account_id: str,
    details: dict[str, Any] | None = None,
) -> bool:
    """Mark the processing job as successfully completed."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    col = get_processing_jobs_collection()

    res = col.update_one(
        {
            "job_id": job_id,
            "account_id": account_id,
            # Prevent race conditions or completing a cancelled/failed job
            "status": {"$in": [JOB_STATE_QUEUED, JOB_STATE_PROCESSING]},
        },
        {
            "$set": {
                "status": JOB_STATE_COMPLETED,
                "current_stage": STAGE_READY,
                "progress": 100,
                "completed_at": now,
                "updated_at": now,
                "completion_details": details or {},
            }
        },
    )
    return res.modified_count > 0


def fail_job(
    job_id: str,
    account_id: str,
    failure_code: str,
    safe_failure_message: str,
) -> bool:
    """Atomically transition the job to FAILED state with a safe message."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    col = get_processing_jobs_collection()

    res = col.update_one(
        {"job_id": job_id, "account_id": account_id},
        {
            "$set": {
                "status": JOB_STATE_FAILED,
                "failure_code": failure_code,
                "safe_failure_message": safe_failure_message,
                "completed_at": now,
                "updated_at": now,
            }
        },
    )
    return res.matched_count > 0


def get_job(job_id: str, account_id: str) -> dict[str, Any] | None:
    """Retrieve job details strictly scoped to authorized account."""
    col = get_processing_jobs_collection()
    return col.find_one({"job_id": job_id, "account_id": account_id}, {"_id": 0})


def list_jobs(account_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """List processing jobs for the authorized account."""
    col = get_processing_jobs_collection()
    return list(col.find({"account_id": account_id}, {"_id": 0}).sort("created_at", -1).limit(limit))


def recover_stale_jobs(timeout_seconds: int = 300) -> int:
    """Recover jobs stuck in PROCESSING state due to ungraceful worker/server restarts."""
    col = get_processing_jobs_collection()
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=timeout_seconds)).isoformat()

    # Find jobs in PROCESSING state whose heartbeat_at is older than cutoff
    stale_query = {
        "status": JOB_STATE_PROCESSING,
        "$or": [
            {"heartbeat_at": {"$lt": cutoff}},
            {"heartbeat_at": {"$exists": False}, "created_at": {"$lt": cutoff}},
        ],
    }

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    res = col.update_many(
        stale_query,
        {
            "$set": {
                "status": JOB_STATE_FAILED,
                "failure_code": "STALE_JOB_TIMEOUT",
                "safe_failure_message": "Processing timed out or host restarted. Safe recovery applied.",
                "completed_at": now,
                "updated_at": now,
            }
        },
    )
    if res.modified_count > 0:
        logger.warning("Recovered %d stale processing jobs.", res.modified_count)
    return res.modified_count
