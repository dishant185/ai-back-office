import logging
import os
from pathlib import Path
import secrets

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent

for env_path in (BACKEND_DIR / ".env", ROOT_DIR / ".env"):
    if env_path.exists():
        load_dotenv(env_path)


class Settings:
    app_name: str
    app_version: str
    environment: str
    api_prefix: str
    frontend_url: str
    cors_allowed_origins: list[str]
    upload_dir: str
    max_upload_size_mb: int
    max_upload_size_bytes: int
    allowed_extensions: list[str]
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    ai_enabled: bool
    llm_provider: str
    llm_api_key: str
    llm_model: str
    llm_base_url: str
    llm_timeout: int
    mongodb_url: str
    mongodb_db_name: str

    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "AI Back-Office Copilot")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.api_prefix = os.getenv("API_PREFIX", "/api")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.upload_dir = os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "data" / "uploads"))
        self.max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
        self.max_upload_size_bytes = self.max_upload_size_mb * 1024 * 1024
        self.allowed_extensions = ["csv", "xlsx", "xls"]

        # CORS Origins Allow-List (no wildcards with credentials)
        raw_allowed = os.getenv("ALLOWED_ORIGINS", "")
        origins = [orig.strip() for orig in raw_allowed.split(",") if orig.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        for default_orig in ("http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"):
            if default_orig not in origins:
                origins.append(default_orig)
        self.cors_allowed_origins = origins

        # Database Settings (PostgreSQL with SQLite development fallback)
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

        # Security & JWT Settings
        raw_jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not raw_jwt_secret:
            if self.environment == "production":
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY environment variable is not set. "
                    "In production, a persistent cryptographic secret key (e.g. 64-char hex) must be provided."
                )
            else:
                self.jwt_secret_key = secrets.token_hex(32)
                logger.warning(
                    "SECURITY WARNING: JWT_SECRET_KEY is not set in environment. "
                    "Generated ephemeral per-process secret for development. "
                    "Authentication tokens will NOT survive application restarts!"
                )
        else:
            self.jwt_secret_key = raw_jwt_secret

        self.jwt_algorithm = "HS256"
        self.jwt_access_token_expire_minutes = 60 * 24 * 7  # 7 days

        # External LLM Provider Settings
        self.ai_enabled = os.getenv("AI_ENABLED", "true").lower() in ("true", "1", "yes")
        self.llm_provider = os.getenv("LLM_PROVIDER", os.getenv("AI_PROVIDER", "generic")).lower()
        self.llm_api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.llm_model = os.getenv("LLM_MODEL", os.getenv("LOCAL_AI_MODEL", "gpt-4o-mini"))
        self.llm_base_url = os.getenv("LLM_BASE_URL", os.getenv("LOCAL_AI_BASE_URL", "http://127.0.0.1:8080/v1"))
        self.llm_timeout = int(os.getenv("LLM_TIMEOUT", os.getenv("LOCAL_AI_TIMEOUT", "60")))

        # Legacy MongoDB compatibility flag
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "ai_backoffice")

    @property
    def service_name(self) -> str:
        return self.app_name.lower().replace(" ", "-")


settings = Settings()
