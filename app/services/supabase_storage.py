"""Supabase Storage client for evidence snapshots."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class StorageUploadResult:
    """Result of a storage upload."""

    path: str
    content_type: str
    etag: str | None = None


class SupabaseStorageClient:
    """Minimal Supabase Storage client (REST)."""

    def __init__(
        self,
        url: str | None = None,
        service_role_key: str | None = None,
        bucket: str | None = None,
    ) -> None:
        self.url = url or settings.supabase_url
        self.service_role_key = service_role_key or settings.supabase_service_role_key
        self.bucket = bucket or settings.supabase_storage_bucket

        if not self.url or not self.service_role_key or not self.bucket:
            raise ValueError(
                "Supabase Storage is not configured. "
                "Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_STORAGE_BUCKET."
            )

    def upload_bytes(self, path: str, data: bytes, content_type: str) -> StorageUploadResult:
        """Upload raw bytes to Supabase Storage."""
        endpoint = f"{self.url}/storage/v1/object/{self.bucket}/{path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apikey": self.service_role_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        try:
            response = httpx.post(endpoint, headers=headers, content=data, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Supabase Storage upload failed", status=exc.response.status_code)
            raise ValueError(f"Supabase Storage upload failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("Supabase Storage upload error", error=str(exc))
            raise ValueError("Supabase Storage upload failed") from exc

        return StorageUploadResult(
            path=path,
            content_type=content_type,
            etag=response.headers.get("etag"),
        )

    def download_bytes(self, path: str) -> bytes:
        """Download raw bytes from Supabase Storage."""
        endpoint = f"{self.url}/storage/v1/object/{self.bucket}/{path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apikey": self.service_role_key,
        }

        try:
            response = httpx.get(endpoint, headers=headers, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Supabase Storage download failed", status=exc.response.status_code)
            raise ValueError(f"Supabase Storage download failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("Supabase Storage download error", error=str(exc))
            raise ValueError("Supabase Storage download failed") from exc

        return response.content
