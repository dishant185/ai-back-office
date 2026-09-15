from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class UploadService:
    def __init__(self, upload_dir: str | None = None) -> None:
        base_dir = Path(upload_dir) if upload_dir else Path(settings.upload_dir)
        self.upload_dir = base_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def generate_safe_filename(self, original_name: str) -> str:
        safe_name = Path(original_name).name
        if not safe_name:
            safe_name = f"upload-{uuid.uuid4().hex}"
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix.lower()
        unique_name = f"{stem}-{uuid.uuid4().hex}{suffix}"
        return unique_name

    def save_upload(self, file: UploadFile) -> tuple[str, str, int]:
        safe_name = self.generate_safe_filename(file.filename or "upload")
        file_path = self.upload_dir / safe_name
        content = file.file.read()
        file_path.write_bytes(content)
        return safe_name, str(file_path), len(content)

    def is_allowed_extension(self, filename: str) -> bool:
        suffix = Path(filename).suffix.lower().lstrip(".")
        return suffix in settings.allowed_extensions

    def is_allowed_file_size(self, size_bytes: int) -> bool:
        return size_bytes <= settings.max_upload_size_bytes


upload_service = UploadService()
