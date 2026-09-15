from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent

for env_path in (BACKEND_DIR / ".env", ROOT_DIR / ".env"):
    if env_path.exists():
        load_dotenv(env_path)


class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Back-Office Copilot")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    upload_dir: str = os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "data" / "uploads"))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    max_upload_size_bytes: int = max_upload_size_mb * 1024 * 1024
    allowed_extensions: list[str] = [
        "csv",
        "xlsx",
        "xls",
    ]

    # MongoDB Settings
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "ai_backoffice")

    # Security & JWT Settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "copilot-executive-secret-token-32char-min-enterprise-prod")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    @property
    def service_name(self) -> str:
        return self.app_name.lower().replace(" ", "-")


settings = Settings()
