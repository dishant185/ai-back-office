"""Account-wide Dataset Knowledge Registry.

Provides fast in-memory caching and persistent MongoDB backing
for dataset knowledge packages.
"""
from __future__ import annotations

import logging
from typing import Any
import pandas as pd

from app.data.knowledge.models import DatasetKnowledgePackage
from app.data.knowledge.builder import build_dataset_knowledge
from app.db.repositories.knowledge_repository import KnowledgeRepository
from app.db.repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)


class DatasetKnowledgeRegistry:
    """Registry maintaining knowledge packages for all datasets."""

    def __init__(self) -> None:
        self._cache: dict[str, DatasetKnowledgePackage] = {}
        self._knw_repo = KnowledgeRepository()
        self._ds_repo = DatasetRepository()

    def get_knowledge(self, dataset_id: str, account_id: str | None = None) -> DatasetKnowledgePackage | None:
        cache_key = f"{account_id or 'all'}:{dataset_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Check DB
        doc = self._knw_repo.get_knowledge(dataset_id, account_id)
        if doc and "package" in doc:
            pkg = DatasetKnowledgePackage(**doc["package"])
            self._cache[cache_key] = pkg
            return pkg

        return None

    def register_dataset(
        self,
        frame: pd.DataFrame,
        dataset_id: str,
        account_id: str,
        file_name: str,
        file_type: str = "csv",
    ) -> DatasetKnowledgePackage:
        pkg = build_dataset_knowledge(
            frame=frame,
            dataset_id=dataset_id,
            account_id=account_id,
            file_name=file_name,
            file_type=file_type,
        )

        # Save to DB
        try:
            self._knw_repo.save_knowledge(dataset_id, account_id, pkg.to_dict())
        except Exception as exc:
            logger.warning("Could not persist knowledge package to MongoDB: %s", exc)

        cache_key = f"{account_id}:{dataset_id}"
        self._cache[cache_key] = pkg
        return pkg

    def clear_cache(self, dataset_id: str | None = None) -> None:
        if dataset_id:
            keys_to_del = [k for k in self._cache if k.endswith(f":{dataset_id}")]
            for k in keys_to_del:
                del self._cache[k]
        else:
            self._cache.clear()


# Global registry singleton
knowledge_registry = DatasetKnowledgeRegistry()
