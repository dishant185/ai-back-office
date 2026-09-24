"""AI Business Analyst orchestrator.

Integrates Question Understanding, Structured Query Planning, Query Validation,
Deterministic DuckDB/Pandas Execution, Verified Results, Strict Result Validation,
and Grounded Response Generation across Fast, NLP, and LLM paths.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
import pandas as pd

from app.analytics.engine import AnalyticsEngine
from app.analyst.answer_builder import AnswerBuilder
from app.analyst.context_manager import ContextManager
from app.analyst.message_router import MessageRouter
from app.analyst.query_planner import QueryPlanner
from app.analyst.query_validator import QueryValidator
from app.ai.llm_service import LLMService
from app.ai.validators import AnalystResponse
from app.data.loader import load_tabular_file
from app.data.semantic.schema_builder import SemanticSchemaBuilder
from app.db.repositories.dataset_repository import DatasetRepository
from app.validation.result_validator import ResultValidator

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


def _split_sub_questions(question: str) -> list[str]:
    """Decompose compound messages containing multiple questions into independent inquiries."""
    raw_lines = [line.strip() for line in question.split("\n") if line.strip()]
    parts: list[str] = []
    for l in raw_lines:
        q_splits = [p.strip() + "?" for p in l.split("?") if p.strip()]
        if len(q_splits) > 1:
            parts.extend(q_splits)
        else:
            parts.append(l)

    if len(parts) > 1 and all(len(sq) > 4 for sq in parts):
        return parts

    # Check for compound sentence with multiple interrogatives: e.g. "What is X, which is Y, and what is Z?"
    single_q = parts[0] if parts else question.strip()
    compound_pattern = r"(?:,\s*(?:and\s+)?|\s+and\s+)(?=(?:what|which|how|who|where|is\s+there)\b)"
    compound_splits = re.split(compound_pattern, single_q, flags=re.IGNORECASE)
    if len(compound_splits) > 1 and all(len(cs.strip()) > 5 for cs in compound_splits):
        return [cs.strip() + ("?" if not cs.strip().endswith("?") else "") for cs in compound_splits]

    return [single_q]


async def _analyze_single_question(
    q: str,
    frame: pd.DataFrame,
    schema: Any,
    dataset_id: str,
    *,
    conversation_history: list[dict[str, Any]] | None = None,
) -> AnalystResponse:
    # 1. Resolve multi-turn references (e.g. 'its', 'them', 'the second one')
    resolved_q, context_hints = ContextManager.resolve_followup(q, conversation_history or [])

    # 2. 3-Level Message Router
    routing = MessageRouter.route(resolved_q, schema, context_hints)

    # 3. Plan structured query
    plan = QueryPlanner.plan(resolved_q, schema, context_hints)
    plan.execution_path = routing.path

    # 4. Validate query plan (safety, bounds, schema compliance)
    validated_plan = QueryValidator.validate(plan, schema)

    # 5. Deterministic Analytics Engine execution
    engine = AnalyticsEngine(frame)
    verified = engine.execute_query_plan(validated_plan, frame, schema, dataset_id, resolved_q)

    # 6. Strict Query-Result Validation
    is_valid_result = ResultValidator.validate(validated_plan, verified)

    # 7. Response generation based on routing path
    if routing.path == "PATH_A_FAST_DETERMINISTIC" or not is_valid_result or verified.verification_status in ("unavailable", "clarification", "rejected"):
        response_payload = AnswerBuilder.build_answer(verified)
        response_payload["ai_status"] = "VERIFIED_ANALYTICS_ONLY"
    else:
        # PATH_B or PATH_C: Grounded LLM response generation with strict verification
        try:
            response_payload = await LLMService.generate_grounded_response(
                resolved_q,
                verified,
                conversation_history,
            )
        except Exception as exc:
            logger.warning("LLM response generation failed, falling back to deterministic response: %s", exc)
            response_payload = AnswerBuilder.build_answer(verified)
            response_payload["ai_status"] = "VERIFIED_ANALYTICS_ONLY"

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
        limitations=[] if not (verified.is_unavailable or verified.verification_status == "rejected") else [verified.error_message or "Metric unavailable"],
        entity=str(entity_val) if entity_val else None,
        dimension=str(dimension_val) if dimension_val else None,
        measure=str(measure_val) if measure_val else None,
        ai_status=response_payload.get("ai_status", "VERIFIED_ANALYTICS_ONLY"),
    )


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

    # 2. Check for multiple independent questions in one user message
    sub_questions = _split_sub_questions(question)

    if len(sub_questions) > 1:
        answers = []
        combined_sources: list[Any] = []
        combined_limitations: list[str] = []
        for idx, sq in enumerate(sub_questions, 1):
            sub_resp = await _analyze_single_question(
                sq,
                frame,
                schema,
                dataset_id,
                conversation_history=conversation_history,
            )
            answers.append(f"{idx}. {sub_resp.answer}")
            combined_sources.extend(sub_resp.sources)
            combined_limitations.extend(sub_resp.limitations)

        return AnalystResponse(
            answer="\n\n".join(answers),
            sources=combined_sources,
            insights=[],
            recommendations=[],
            limitations=combined_limitations,
            ai_status="VERIFIED_ANALYTICS_ONLY",
        )

    return await _analyze_single_question(
        question,
        frame,
        schema,
        dataset_id,
        conversation_history=conversation_history,
    )
