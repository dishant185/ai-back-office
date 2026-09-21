from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.analytics.engine import AnalyticsEngine
from app.core.config import settings
from app.data.loader import DataLoader
from app.schemas.analytics import AnalyticsRunRequest, AnalyticsRunResponse

router = APIRouter()


@router.post("/run", response_model=AnalyticsRunResponse)
@router.post("/analytics/run", response_model=AnalyticsRunResponse)
def run_analytics(payload: AnalyticsRunRequest) -> AnalyticsRunResponse:
    dataset_path = Path(settings.upload_dir) / payload.dataset_id
    if not dataset_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {payload.dataset_id} was not found.",
        )

    frame = DataLoader().load_file(dataset_path)
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


class QueryRequest(BaseModel):
    question: str
    dataset_id: str


class PlanRequest(BaseModel):
    question: str
    dataset_id: str


def _load_frame_helper(dataset_id: str):
    from app.db.repositories.dataset_repository import DatasetRepository
    from app.data.loader import load_tabular_file
    repo = DatasetRepository()
    doc = repo.get_by_id(dataset_id)
    if doc and doc.get("file_path") and Path(doc["file_path"]).exists():
        return load_tabular_file(Path(doc["file_path"]))
    for d in [Path("data/uploads"), Path("../data/uploads")]:
        if d.exists():
            for f in d.glob("*.*"):
                if dataset_id in f.name or f.stem == dataset_id:
                    return load_tabular_file(f)
    return None


@router.post("/query")
def execute_analytics_query(payload: QueryRequest) -> dict:
    """Execute a deterministic query plan for a natural-language question."""
    from app.analyst.query_planner import QueryPlanner
    from app.analyst.query_validator import QueryValidator
    from app.data.semantic.schema_builder import SemanticSchemaBuilder

    frame = _load_frame_helper(payload.dataset_id)
    if frame is None:
        raise HTTPException(status_code=404, detail=f"Dataset {payload.dataset_id} not found.")

    schema = SemanticSchemaBuilder.build(frame)
    plan = QueryPlanner.plan(payload.question, schema)
    validated = QueryValidator.validate(plan, schema)
    engine = AnalyticsEngine(frame)
    verified = engine.execute_query_plan(validated, frame, schema, payload.dataset_id, payload.question)
    return verified.model_dump()


@router.post("/plan")
def plan_analytics_query(payload: PlanRequest) -> dict:
    """Generate a structured QueryPlan without executing it."""
    from app.analyst.query_planner import QueryPlanner
    from app.analyst.query_validator import QueryValidator
    from app.data.semantic.schema_builder import SemanticSchemaBuilder

    frame = _load_frame_helper(payload.dataset_id)
    if frame is None:
        raise HTTPException(status_code=404, detail=f"Dataset {payload.dataset_id} not found.")

    schema = SemanticSchemaBuilder.build(frame)
    plan = QueryPlanner.plan(payload.question, schema)
    validated = QueryValidator.validate(plan, schema)
    return validated.model_dump()


@router.get("/capabilities/{dataset_id}")
def get_analytics_capabilities(dataset_id: str) -> dict:
    """Get dynamic analytics capabilities discovered for dataset."""
    from app.ai.dataset.capability_detector import CapabilityDetector
    from app.data.semantic.schema_builder import SemanticSchemaBuilder
    from app.ai.dataset.semantic_mapper import SemanticMapper
    from app.ai.dataset.profiler import DatasetProfiler

    frame = _load_frame_helper(dataset_id)
    if frame is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    prof = DatasetProfiler.profile_dataframe(frame)
    mappings = SemanticMapper.map_columns(prof.columns)
    caps = CapabilityDetector.detect_capabilities(mappings)
    return {
        "dataset_id": dataset_id,
        "capabilities": caps,
    }

