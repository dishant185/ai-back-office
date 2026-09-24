"""Analytics execution endpoints with strict multi-tenant authorization."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.analytics.engine import AnalyticsEngine
from app.core.deps import AuthorizedScope, get_authorized_scope
from app.data.loader import DataLoader, load_tabular_file
from app.db.repositories.dataset_repository import DatasetRepository
from app.schemas.analytics import AnalyticsRunRequest, AnalyticsRunResponse

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    dataset_id: str


class PlanRequest(BaseModel):
    question: str
    dataset_id: str


def _load_frame_helper(dataset_id: str, account_id: str):
    repo = DatasetRepository()
    doc = repo.get_by_id(dataset_id, account_id=account_id)
    if doc and (doc.get("file_path") or doc.get("saved_path")):
        fpath = doc.get("file_path") or doc.get("saved_path")
        if fpath and Path(fpath).exists():
            return load_tabular_file(Path(fpath))
    return None


@router.post("/run", response_model=AnalyticsRunResponse)
@router.post("/analytics/run", response_model=AnalyticsRunResponse)
def run_analytics(
    payload: AnalyticsRunRequest,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> AnalyticsRunResponse:
    frame = _load_frame_helper(payload.dataset_id, scope.account_id)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {payload.dataset_id} was not found or unauthorized.",
        )

    engine = AnalyticsEngine(frame)
    result = engine.analyze(frame)

    return AnalyticsRunResponse(
        success=True,
        dataset_id=payload.dataset_id,
        profile=result.profile,
        capabilities=result.capabilities,
        summary=result.summary,
        metrics=result.metrics,
        trends=result.trends,
        anomalies=result.anomalies,
        notes=result.notes,
    )


@router.post("/query")
def execute_analytics_query(
    payload: QueryRequest,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Execute a deterministic query plan for a natural-language question."""
    from app.analyst.query_planner import QueryPlanner
    from app.analyst.query_validator import QueryValidator
    from app.data.semantic.schema_builder import SemanticSchemaBuilder

    frame = _load_frame_helper(payload.dataset_id, scope.account_id)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {payload.dataset_id} not found or unauthorized.",
        )

    schema = SemanticSchemaBuilder.build(frame)
    plan = QueryPlanner.plan(payload.question, schema)
    validated = QueryValidator.validate(plan, schema)
    engine = AnalyticsEngine(frame)
    verified = engine.execute_query_plan(validated, frame, schema, payload.dataset_id, payload.question)
    return verified.model_dump()


@router.post("/plan")
def plan_analytics_query(
    payload: PlanRequest,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Generate a structured QueryPlan without executing it."""
    from app.analyst.query_planner import QueryPlanner
    from app.analyst.query_validator import QueryValidator
    from app.data.semantic.schema_builder import SemanticSchemaBuilder

    frame = _load_frame_helper(payload.dataset_id, scope.account_id)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {payload.dataset_id} not found or unauthorized.",
        )

    schema = SemanticSchemaBuilder.build(frame)
    plan = QueryPlanner.plan(payload.question, schema)
    validated = QueryValidator.validate(plan, schema)
    return validated.model_dump()


@router.get("/capabilities/{dataset_id}")
def get_analytics_capabilities(
    dataset_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get dynamic analytics capabilities discovered for dataset."""
    from app.ai.dataset.capability_detector import CapabilityDetector
    from app.ai.dataset.profiler import DatasetProfiler
    from app.ai.dataset.semantic_mapper import SemanticMapper

    frame = _load_frame_helper(dataset_id, scope.account_id)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found or unauthorized.",
        )

    prof = DatasetProfiler.profile_dataframe(frame)
    mappings = SemanticMapper.map_columns(prof.columns)
    caps = CapabilityDetector.detect_capabilities(mappings)
    return {
        "dataset_id": dataset_id,
        "capabilities": caps,
    }
