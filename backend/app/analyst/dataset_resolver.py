"""Account-wide Dataset Resolver.

Resolves which dataset a user query refers to.
Safely prompts for clarification when multiple datasets match instead of guessing.
"""
from __future__ import annotations

import re
from typing import Any
from app.db.repositories.dataset_repository import DatasetRepository


class DatasetResolver:
    """Resolves target dataset within an authenticated account."""

    @classmethod
    def resolve(
        cls,
        account_id: str,
        question: str,
        current_dataset_id: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Returns (resolved_dataset_id, clarification_question).

        If ambiguous, returns (None, clarification_prompt).
        """
        repo = DatasetRepository()
        account_datasets = repo.list_datasets(account_id=account_id)

        if not account_datasets:
            return None, "No datasets found in your account. Please upload a CSV or Excel file first."

        q_lower = question.lower()

        # 1. Check if user explicitly mentioned a filename (e.g. "sales_2025.csv")
        for ds in account_datasets:
            fname = (ds.get("file_name") or ds.get("filename") or "").lower()
            if fname and fname in q_lower:
                return ds.get("dataset_id") or ds.get("upload_id"), None
            # Also check without extension
            fname_stem = fname.rsplit(".", 1)[0]
            if fname_stem and len(fname_stem) > 4 and fname_stem in q_lower:
                return ds.get("dataset_id") or ds.get("upload_id"), None

        # 2. Check domain / capability matching across account datasets
        hr_keywords = ["employee", "employees", "attrition", "leave", "staff", "joining year", "experience in current domain", "education"]
        sales_keywords = ["sales", "revenue", "orders", "units sold", "discount", "salesperson", "commercial"]
        inventory_keywords = ["stock", "inventory", "warehouse", "pallets", "sku"]

        matching_datasets = []
        is_hr_q = any(k in q_lower for k in hr_keywords)
        is_sales_q = any(k in q_lower for k in sales_keywords)
        is_inv_q = any(k in q_lower for k in inventory_keywords)

        for ds in account_datasets:
            fname = (ds.get("file_name") or ds.get("filename") or "").lower()
            prof = (ds.get("profile") or ds.get("domain") or "").lower()
            if is_hr_q and (prof == "hr" or any(k in fname for k in ["employee", "staff", "hr"])):
                matching_datasets.append(ds)
            elif is_sales_q and (prof == "sales" or any(k in fname for k in ["sales", "revenue", "order"])):
                matching_datasets.append(ds)
            elif is_inv_q and (prof == "inventory" or any(k in fname for k in ["inventory", "stock", "warehouse"])):
                matching_datasets.append(ds)

        if len(matching_datasets) == 1:
            ds = matching_datasets[0]
            return ds.get("dataset_id") or ds.get("upload_id"), None
        elif len(matching_datasets) > 1:
            names = [ds.get("file_name") or ds.get("filename") for ds in matching_datasets]
            clarification = f"I found multiple datasets that could answer this ({', '.join(names)}). Which one should I use?"
            return None, clarification

        # 3. If current_dataset_id is active and valid, use it
        if current_dataset_id:
            for ds in account_datasets:
                if (ds.get("dataset_id") == current_dataset_id) or (ds.get("upload_id") == current_dataset_id):
                    return current_dataset_id, None

        # 4. If there is only one dataset in the account, use it automatically
        if len(account_datasets) == 1:
            ds = account_datasets[0]
            return ds.get("dataset_id") or ds.get("upload_id"), None

        # 5. Default to the most recently created dataset
        latest = account_datasets[0]
        return latest.get("dataset_id") or latest.get("upload_id"), None
