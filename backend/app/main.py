from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.db.indexes import init_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    app_logger = logging.getLogger(__name__)

    # Initialize MongoDB multi-tenant indexes
    try:
        init_indexes()
    except Exception as exc:
        app_logger.warning("MongoDB index initialization error: %s", exc)

    # Startup LLM reachability verification
    if settings.ai_enabled:
        try:
            prov = get_llm_provider()
            health = await prov.health_check(probe=True)
            if not health.get("connected", False):
                app_logger.warning(
                    "AI SUBSYSTEM WARNING: AI_ENABLED=True but external LLM provider '%s' is unreachable or unconfigured (reason: %s). "
                    "Executive summaries and AI chat will operate in verified deterministic mode.",
                    settings.llm_provider,
                    health.get("details", {}).get("error") or health.get("details", {}).get("reason") or "unreachable",
                )
            else:
                app_logger.info("AI Subsystem connected successfully to provider '%s' (model: %s).", settings.llm_provider, settings.llm_model)
        except Exception as exc:
            app_logger.warning("AI Subsystem probe encountered an error on startup: %s", exc)

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Back-Office Copilot API foundation",
    docs_url="/docs",
    redoc_url=False,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


from app.ai.provider import get_llm_provider
from app.db.database import check_mongo_health
from app.schemas.health import ComponentHealth, HealthResponse, ReadinessResponse, RootResponse


@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        message="AI Back-Office Copilot API",
        version=settings.app_version,
        status="running",
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_health = check_mongo_health()
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.app_version,
        database=ComponentHealth(
            status=db_health["status"],
            connected=db_health["connected"],
            details=db_health,
        ),
    )


@app.get("/readiness", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    db_health = check_mongo_health()
    llm_prov = get_llm_provider()
    llm_health = await llm_prov.health_check(probe=True)

    db_comp = ComponentHealth(
        status=db_health["status"],
        connected=db_health["connected"],
        details=db_health,
    )
    llm_comp = ComponentHealth(
        status=llm_health["status"],
        connected=llm_health.get("connected", False),
        details=llm_health,
    )

    overall_status = "ready"
    if not db_health["connected"] and settings.environment == "production":
        overall_status = "degraded"

    return ReadinessResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.app_version,
        environment=settings.environment,
        database=db_comp,
        llm=llm_comp,
    )


app.include_router(v1_router)
