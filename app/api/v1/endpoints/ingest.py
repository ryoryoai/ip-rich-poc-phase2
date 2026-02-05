"""Ingestion endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import IngestionJob
from app.services.ingestion_service import IngestionService

router = APIRouter()


class IngestItem(BaseModel):
    input_number: str = Field(..., min_length=1)
    input_number_type: str = Field(..., min_length=1)
    target_version_hint: dict | None = None


class IngestRequest(BaseModel):
    numbers: list[str] | None = None
    input_type: str = "publication"
    items: list[IngestItem] | None = None
    priority: int = 5
    force_refresh: bool = False
    source_preference: str | None = None
    idempotency_key: str | None = None
    target_version_hint: dict | None = None


class IngestResponse(BaseModel):
    job_id: str
    queued_count: int
    status: str


@router.post("", response_model=IngestResponse)
def create_ingest_job(
    request: IngestRequest,
    db: Annotated[Session, Depends(get_db)],
) -> IngestResponse:
    """Create an ingestion job."""
    if not request.items and not request.numbers:
        raise HTTPException(status_code=400, detail="numbers or items is required")

    if request.items:
        items = [
            {
                "input_number": item.input_number,
                "input_number_type": item.input_number_type,
                "target_version_hint": item.target_version_hint,
            }
            for item in request.items
        ]
    else:
        items = [
            {
                "input_number": number.strip(),
                "input_number_type": request.input_type,
                "target_version_hint": request.target_version_hint,
            }
            for number in (request.numbers or [])
            if number.strip()
        ]

    if not items:
        raise HTTPException(status_code=400, detail="No valid numbers provided")

    service = IngestionService(db)
    job = service.create_job(
        items=items,
        priority=request.priority,
        force_refresh=request.force_refresh,
        source_preference=request.source_preference,
        idempotency_key=request.idempotency_key,
    )

    return IngestResponse(
        job_id=str(job.job_id),
        queued_count=len(job.items),
        status=job.status,
    )


class IngestionJobItemResponse(BaseModel):
    job_item_id: str
    input_number: str
    input_number_type: str
    status: str
    retry_count: int
    error_code: str | None
    error_detail: str | None
    target_version_hint: dict | None


class IngestionJobResponse(BaseModel):
    job_id: str
    status: str
    priority: int
    force_refresh: bool
    source_preference: str | None
    retry_count: int
    max_retries: int
    error_code: str | None
    error_detail: str | None
    created_at: str | None
    started_at: str | None
    finished_at: str | None
    items: list[IngestionJobItemResponse]


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def get_ingest_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> IngestionJobResponse:
    """Get ingestion job status."""
    job = db.query(IngestionJob).filter(IngestionJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return IngestionJobResponse(
        job_id=str(job.job_id),
        status=job.status,
        priority=job.priority,
        force_refresh=job.force_refresh,
        source_preference=job.source_preference,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        error_code=job.error_code,
        error_detail=job.error_detail,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        items=[
            IngestionJobItemResponse(
                job_item_id=str(item.job_item_id),
                input_number=item.input_number,
                input_number_type=item.input_number_type,
                status=item.status,
                retry_count=item.retry_count,
                error_code=item.error_code,
                error_detail=item.error_detail,
                target_version_hint=item.target_version_hint,
            )
            for item in job.items
        ],
    )
