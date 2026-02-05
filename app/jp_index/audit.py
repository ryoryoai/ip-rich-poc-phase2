"""Audit logging for JP Index."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import Request

from app.core import get_logger
from app.db.models import JpAuditLog
from app.db.session import SessionLocal

logger = get_logger(__name__)


def _get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def record_audit_log(
    request: Request,
    action: str,
    payload: dict[str, Any],
    resource_id: Optional[str] = None,
) -> None:
    """Persist audit log entry. Failures do not break the request."""
    try:
        with SessionLocal() as db:
            log = JpAuditLog(
                action=action,
                resource_id=resource_id,
                request_path=request.url.path,
                method=request.method,
                client_ip=_get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                payload_json=payload,
            )
            db.add(log)
            db.commit()
    except Exception as exc:
        logger.warning("audit_log_failed", error=str(exc), action=action, resource_id=resource_id)
