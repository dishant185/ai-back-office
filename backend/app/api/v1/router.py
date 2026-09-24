from fastapi import APIRouter

from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.analyst import router as analyst_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.datasets import router as datasets_router
from app.api.v1.endpoints.mappings import router as mappings_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.audit import router as audit_router
from app.core.config import settings
from app.schemas.health import HealthResponse, RootResponse

router = APIRouter(prefix="/api/v1")


@router.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        message="AI Back-Office Copilot API",
        version=settings.app_version,
        status="running",
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.app_version,
    )


router.include_router(auth_router, prefix="/auth")
router.include_router(uploads_router)
router.include_router(datasets_router)
router.include_router(mappings_router, prefix="/mappings")
router.include_router(analytics_router, prefix="/analytics")
router.include_router(reports_router, prefix="/reports")
router.include_router(dashboard_router, prefix="/dashboard")
router.include_router(ai_router, prefix="/ai")
router.include_router(analyst_router, prefix="/analyst")
router.include_router(jobs_router)
router.include_router(audit_router)


