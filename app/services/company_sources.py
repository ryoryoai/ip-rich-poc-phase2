"""External company data sources (gBizINFO / EDINET)."""

from __future__ import annotations

from typing import Any

import httpx

from app.core import get_logger
from app.core.config import settings

logger = get_logger(__name__)


def _get_nested(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def extract_fields(payload: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """Extract mapped fields using dot-path mapping."""
    extracted: dict[str, Any] = {}
    for field_name, path in mapping.items():
        value = _get_nested(payload, path)
        if value is not None:
            extracted[field_name] = value
    return extracted


class GbizinfoClient:
    """Minimal gBizINFO API client."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_key_header: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.gbizinfo_api_base_url
        self.api_key = api_key or settings.gbizinfo_api_key
        self.api_key_header = api_key_header or settings.gbizinfo_api_key_header

        if not self.base_url or not self.api_key:
            raise ValueError("gBizINFO API is not configured")

    def fetch_by_corporate_number(self, corporate_number: str) -> dict[str, Any]:
        if "{corporate_number}" in self.base_url:
            url = self.base_url.format(corporate_number=corporate_number)
        else:
            url = f"{self.base_url.rstrip('/')}/{corporate_number}"

        headers = {
            self.api_key_header: self.api_key,
            "User-Agent": settings.collection_user_agent,
        }

        response = httpx.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


class EdinetClient:
    """Minimal EDINET API client."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_key_header: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.edinet_api_base_url
        self.api_key = api_key or settings.edinet_api_key
        self.api_key_header = api_key_header or settings.edinet_api_key_header

        if not self.base_url or not self.api_key:
            raise ValueError("EDINET API is not configured")

    def fetch(self, edinet_code: str) -> dict[str, Any]:
        if "{edinet_code}" in self.base_url:
            url = self.base_url.format(edinet_code=edinet_code)
        else:
            url = self.base_url

        headers = {
            self.api_key_header: self.api_key,
            "User-Agent": settings.collection_user_agent,
        }

        params = None
        if "{edinet_code}" not in self.base_url:
            params = {"edinetCode": edinet_code}

        response = httpx.get(url, headers=headers, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()
