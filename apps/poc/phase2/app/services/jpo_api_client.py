"""JPO API client (generic)."""

from __future__ import annotations

from urllib.parse import urljoin

import httpx

from app.core import get_logger, settings

logger = get_logger(__name__)


class JpoApiClient:
    """Minimal JPO API client.

    This is a generic wrapper and expects a base URL + API key.
    Actual endpoint paths are supplied via hints.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.jpo_api_base_url or "").rstrip("/")
        self.api_key = api_key or settings.jpo_api_key
        self.timeout_seconds = timeout_seconds or settings.jpo_api_timeout_seconds

        if not self.base_url or not self.api_key:
            raise ValueError("JPO API is not configured")

    def fetch_bytes(self, path_or_url: str) -> bytes:
        """Fetch raw bytes from the JPO API."""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = urljoin(f"{self.base_url}/", path_or_url.lstrip("/"))

        if not url.startswith(self.base_url):
            raise ValueError("JPO API URL must be under configured base URL")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
        }

        try:
            response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("JPO API request failed", status=exc.response.status_code)
            raise ValueError(f"JPO API request failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("JPO API request error", error=str(exc))
            raise ValueError("JPO API request failed") from exc

        return response.content
