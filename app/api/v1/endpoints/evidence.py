"""Evidence endpoints (upload and metadata)."""

from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Evidence
from app.services.supabase_storage import SupabaseStorageClient

router = APIRouter()


class EvidenceCreateRequest(BaseModel):
    url: str = Field(..., min_length=1)
    source_type: str | None = None
    title: str | None = None
    quote_text: str | None = None
    content_base64: str | None = None
    content_type: str | None = None
    raw: dict | None = None


@router.post("")
def create_evidence(
    request: EvidenceCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create an evidence record and optionally upload a snapshot."""
    evidence_id = uuid.uuid4()
    captured_at = datetime.now(timezone.utc)

    content_hash = None
    storage_path = None

    content_type = request.content_type or "application/octet-stream"

    if request.content_base64:
        try:
            content_bytes = base64.b64decode(request.content_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid base64 content") from exc

        content_hash = hashlib.sha256(content_bytes).hexdigest()
        extension = _guess_extension(content_type)
        storage_path = f"evidence/{evidence_id}.{extension}"

        try:
            storage = SupabaseStorageClient()
            storage.upload_bytes(storage_path, content_bytes, content_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    evidence = Evidence(
        id=evidence_id,
        url=request.url,
        source_type=request.source_type,
        title=request.title,
        quote_text=request.quote_text,
        retrieved_at=captured_at,
        captured_at=captured_at,
        content_hash=content_hash,
        content_type=content_type if request.content_base64 else request.content_type,
        storage_path=storage_path,
        raw=request.raw,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return {
        "evidence_id": str(evidence.id),
        "content_hash": evidence.content_hash,
        "storage_path": evidence.storage_path,
    }


def _guess_extension(content_type: str) -> str:
    if content_type == "text/html":
        return "html"
    if content_type == "application/pdf":
        return "pdf"
    if content_type.startswith("image/"):
        return content_type.split("/", 1)[1]
    return "bin"
