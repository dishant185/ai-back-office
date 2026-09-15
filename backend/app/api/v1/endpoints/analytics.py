from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

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
