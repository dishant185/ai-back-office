"""AI Business Analyst orchestrator.

Integrates Question Understanding, Structured Query Planning, Query Validation,
Deterministic DuckDB/Pandas Execution, Verified Results, and Grounding Enforcement.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import pandas as pd

from app.analytics.engine import AnalyticsEngine
from app.analyst.answer_builder import AnswerBuilder
from app.analyst.context_manager import ContextManager
from app.analyst.query_planner import QueryPlanner
from app.analyst.query_validator import QueryValidator
from app.ai.llm_service import LLMService
from app.ai.validators import AnalystResponse
from app.data.loader import load_tabular_file
from app.data.semantic.schema_builder import SemanticSchemaBuilder
from app.db.repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)


def _load_dataset_frame(dataset_id: str) -> tuple[pd.DataFrame | None, str | None]:
    """Loads DataFrame from dataset_id by looking up repository or disk."""
    repo = DatasetRepository()
    doc = repo.get_by_id(dataset_id)
    if doc and doc.get("file_path"):
        fpath = Path(doc["file_path"])
        if fpath.exists():
            return load_tabular_file(fpath), str(fpath)

    # Fallback to scanning data/uploads
    for uploads_dir in [Path("data/uploads"), Path("../data/uploads")]:
        if uploads_dir.exists():
            for f in uploads_dir.glob("*.*"):
                if dataset_id in f.name or f.stem == dataset_id:
                    return load_tabular_file(f), str(f)
            # Match latest file if dataset_id matches
            files = list(uploads_dir.glob("*.csv")) + list(uploads_dir.glob("*.xlsx"))
            if files:
                for f in files:
                    if f.name.startswith(dataset_id) or dataset_id in f.name:
                        return load_tabular_file(f), str(f)

    return None, None


async def analyze_question(
    question: str,
    dataset_id: str,
    *,
    report_context: dict[str, Any] | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
) -> AnalystResponse:
    """Universal pipeline: Question -> QueryPlan -> Validation -> Analytics -> VerifiedResult -> LLM -> Grounding."""
    frame, file_path = _load_dataset_frame(dataset_id)
    if frame is None:
        return AnalystResponse(
            answer="No dataset is currently loaded. Please upload a CSV or Excel file first.",
            limitations=["Dataset not found"],
        )

    # 1. Build semantic schema
    schema = SemanticSchemaBuilder.build(frame)

    # 2. Resolve multi-turn references (e.g. 'its', 'them')
    resolved_q, context_hints = ContextManager.resolve_followup(question, conversation_history or [])

    # 3. Plan structured query
    plan = QueryPlanner.plan(resolved_q, schema, context_hints)

    # 4. Validate query plan
    validated_plan = QueryValidator.validate(plan, schema)

    # 5. Deterministic Analytics Engine execution
    engine = AnalyticsEngine(frame)
    verified = engine.execute_query_plan(validated_plan, frame, schema, dataset_id, resolved_q)

    # 6. LLM response generation with strict Grounding Validation
    response_payload = await LLMService.generate_grounded_response(
        resolved_q,
        verified,
        conversation_history,
    )

    answer_text = response_payload.get("answer", "")
    sources = response_payload.get("sources", [])

    res = verified.result or {}
    entity_val = res.get("entity") or (res.get("entities")[0] if isinstance(res.get("entities"), list) and res.get("entities") else None)
    dimension_val = res.get("dimension") or (verified.query_plan or {}).get("dimension")
    measure_val = res.get("measure") or (verified.query_plan or {}).get("measure")

    return AnalystResponse(
        answer=answer_text,
        sources=sources,
        insights=[],
        recommendations=[],
        limitations=[] if not verified.is_unavailable else [verified.error_message or "Metric unavailable"],
        entity=str(entity_val) if entity_val else None,
        dimension=str(dimension_val) if dimension_val else None,
        measure=str(measure_val) if measure_val else None,
        ai_status=response_payload.get("ai_status", "VERIFIED_ANALYTICS_ONLY"),
    )
