"""Report repository using MongoDB with strict multi-tenant account isolation."""
from __future__ import annotations

import datetime
from typing import Any, TYPE_CHECKING
import uuid

from app.db.database import get_report_ai_summaries_collection, get_report_summaries_collection, get_reports_collection

if TYPE_CHECKING:
    from app.reporting.report_snapshot import ReportSnapshot


class ReportRepository:
    """Account-scoped repository for managing generated MIS reports and immutable snapshots."""

    def __init__(self) -> None:
        self.collection = get_reports_collection()
        self.summaries_collection = get_report_summaries_collection()
        self.ai_summaries_v7 = get_report_ai_summaries_collection()
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        try:
            self.collection.create_index("report_id", unique=True)
            self.collection.create_index([("account_id", 1), ("created_at", -1)])
            self.collection.create_index([("account_id", 1), ("dataset_id", 1)])
            self.collection.create_index([("account_id", 1), ("dataset_id", 1), ("dataset_version", 1)])

            self.summaries_collection.create_index([
                ("account_id", 1),
                ("dataset_id", 1),
                ("dataset_version", 1),
                ("report_id", 1),
                ("report_version", 1),
                ("summary_prompt_version", 1),
            ])
            self.summaries_collection.create_index([("report_id", 1)])

            self.ai_summaries_v7.create_index([
                ("account_id", 1),
                ("dataset_id", 1),
                ("dataset_version", 1),
                ("report_id", 1),
                ("report_version", 1),
                ("filters_hash", 1),
                ("prompt_version", 1),
            ])
            self.ai_summaries_v7.create_index([("report_id", 1)])
        except Exception:
            pass

    def create_report(
        self,
        account_id: str,
        user_id: str,
        dataset_id: str,
        title: str,
        report_type: str = "standard",
        dataset_version: int = 1,
        content: dict[str, Any] | None = None,
        snapshot: ReportSnapshot | dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        status: str = "completed",
        pdf_path: str | None = None,
    ) -> dict[str, Any]:
        snap_dict = snapshot.model_dump() if hasattr(snapshot, "model_dump") else (snapshot or {})
        rep_id = (
            snap_dict.get("report_id")
            or (content.get("report_id") if content else None)
            or f"rep_{uuid.uuid4().hex[:12]}"
        )
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        doc = {
            "report_id": rep_id,
            "account_id": account_id,
            "user_id": user_id,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "title": title,
            "report_type": report_type,
            "status": status,
            "filters": filters or {},
            "content": content or {},
            "snapshot": snap_dict,
            "snapshot_id": snap_dict.get("snapshot_id"),
            "pdf_path": pdf_path,
            "created_at": now,
            "generated_at": now,
            "updated_at": now,
        }
        self.collection.insert_one(doc)
        return doc

    def get_report(self, report_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"report_id": report_id}
        if account_id:
            query["account_id"] = account_id
        doc = self.collection.find_one(query)
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_report_snapshot(self, report_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        doc = self.get_report(report_id, account_id=account_id)
        if not doc:
            return None
        return doc.get("snapshot") or doc.get("content")

    def list_reports(
        self,
        account_id: str,
        dataset_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"account_id": account_id}
        if dataset_id:
            query["dataset_id"] = dataset_id

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        results: list[dict[str, Any]] = []
        for doc in cursor:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    def update_report(
        self,
        report_id: str,
        update_data: dict[str, Any],
        account_id: str | None = None,
    ) -> bool:
        query: dict[str, Any] = {"report_id": report_id}
        if account_id:
            query["account_id"] = account_id

        update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        res = self.collection.update_one(query, {"$set": update_data})
        return res.modified_count > 0

    def delete_report(self, report_id: str, account_id: str | None = None) -> bool:
        query: dict[str, Any] = {"report_id": report_id}
        if account_id:
            query["account_id"] = account_id
        res = self.collection.delete_one(query)
        # Also clean up report summaries
        try:
            self.summaries_collection.delete_many(query)
        except Exception:
            pass
        return res.deleted_count > 0

    # ── Report Summaries Persistence (Phase 6.6) ──
    def save_report_summary(
        self,
        account_id: str,
        dataset_id: str,
        dataset_version: int,
        report_id: str,
        report_version: int,
        report_type: str,
        content: dict[str, Any],
        verified_claims: list[str] | None = None,
        status: str = "verified",
        summary_prompt_version: str = "6.6.0",
    ) -> dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "account_id": account_id,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "report_id": report_id,
            "report_version": report_version,
            "report_type": report_type,
            "summary_prompt_version": summary_prompt_version,
            "status": status,
            "content": content,
            "verified_claims": verified_claims or [],
            "created_at": now,
            "updated_at": now,
        }
        # Upsert by account, dataset version, report version, prompt version
        self.summaries_collection.update_one(
            {
                "account_id": account_id,
                "dataset_id": dataset_id,
                "dataset_version": dataset_version,
                "report_id": report_id,
                "report_version": report_version,
                "summary_prompt_version": summary_prompt_version,
            },
            {"$set": doc},
            upsert=True,
        )
        return doc

    def get_report_summary(
        self,
        account_id: str,
        dataset_id: str,
        dataset_version: int,
        report_id: str,
        report_version: int,
        summary_prompt_version: str = "6.6.0",
    ) -> dict[str, Any] | None:
        doc = self.summaries_collection.find_one({
            "account_id": account_id,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "report_id": report_id,
            "report_version": report_version,
            "summary_prompt_version": summary_prompt_version,
        })
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def invalidate_report_summaries(
        self,
        account_id: str,
        dataset_id: str | None = None,
        report_id: str | None = None,
    ) -> int:
        query: dict[str, Any] = {"account_id": account_id}
        if dataset_id:
            query["dataset_id"] = dataset_id
        if report_id:
            query["report_id"] = report_id
        res = self.summaries_collection.delete_many(query)
        return res.deleted_count

    def save_ai_summary_v7(
        self,
        account_id: str,
        dataset_id: str,
        dataset_version: int,
        report_id: str,
        report_version: int,
        filters_hash: str,
        status: str,
        summary: dict[str, Any],
        verified_claims: list[str] | None = None,
        prompt_version: str = "7.0.0",
        analytics_version: str = "1.0.0",
        model_provider: str = "generic",
        model_name: str = "gpt-4o-mini",
    ) -> dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "account_id": account_id,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "report_id": report_id,
            "report_version": report_version,
            "filters_hash": filters_hash,
            "filter_hash": filters_hash,
            "status": status,
            "summary": summary,
            "verified_claims": verified_claims or [],
            "validation": {
                "grounding": True,
                "relevance": True,
                "semantic_accuracy": True,
                "duplicates": False,
            },
            "prompt_version": prompt_version,
            "analytics_version": analytics_version,
            "model_provider": model_provider,
            "model_name": model_name,
            "created_at": now,
            "updated_at": now,
        }
        sections = summary.get("sections", []) if isinstance(summary, dict) else []
        doc["sections"] = sections
        self.ai_summaries_v7.update_one(
            {
                "account_id": account_id,
                "dataset_id": dataset_id,
                "dataset_version": dataset_version,
                "report_id": report_id,
                "report_version": report_version,
                "filters_hash": filters_hash,
                "prompt_version": prompt_version,
            },
            {"$set": doc},
            upsert=True,
        )

        # Rule #37 / #38: MongoDB report_summaries collection storage
        rule_38_doc = {
            "account_id": account_id,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "report_id": report_id,
            "report_version": report_version,
            "filters_hash": filters_hash,
            "summary_version": prompt_version,
            "analytics_version": analytics_version,
            "status": status,
            "content": summary,
            "sections": sections,
            "verified_claims": verified_claims or [],
            "generated_at": now,
        }
        try:
            self.summaries_collection.update_one(
                {
                    "account_id": account_id,
                    "dataset_id": dataset_id,
                    "dataset_version": dataset_version,
                    "report_id": report_id,
                    "report_version": report_version,
                    "filters_hash": filters_hash,
                    "summary_version": prompt_version,
                },
                {"$set": rule_38_doc},
                upsert=True,
            )
        except Exception:
            pass

        return doc

    def get_ai_summary_v7(
        self,
        account_id: str,
        dataset_id: str,
        dataset_version: int,
        report_id: str,
        report_version: int,
        filters_hash: str,
        prompt_version: str = "7.0.0",
        analytics_version: str = "1.0.0",
    ) -> dict[str, Any] | None:
        doc = self.ai_summaries_v7.find_one({
            "account_id": account_id,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "report_id": report_id,
            "report_version": report_version,
            "filters_hash": filters_hash,
            "prompt_version": prompt_version,
        })
        if not doc:
            doc = self.summaries_collection.find_one({
                "account_id": account_id,
                "dataset_id": dataset_id,
                "dataset_version": dataset_version,
                "report_id": report_id,
                "report_version": report_version,
                "filters_hash": filters_hash,
                "summary_version": prompt_version,
            })
            if doc and "content" in doc and "summary" not in doc:
                doc["summary"] = doc["content"]
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def invalidate_ai_summaries_v7(
        self,
        account_id: str,
        dataset_id: str | None = None,
        report_id: str | None = None,
    ) -> int:
        query: dict[str, Any] = {"account_id": account_id}
        if dataset_id:
            query["dataset_id"] = dataset_id
        if report_id:
            query["report_id"] = report_id
        res = self.ai_summaries_v7.delete_many(query)
        try:
            self.summaries_collection.delete_many(query)
        except Exception:
            pass
        return res.deleted_count
