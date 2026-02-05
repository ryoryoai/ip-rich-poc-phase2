"""Job status endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.endpoints.ingest import IngestionJobResponse, IngestionJobItemResponse
from app.db.models import IngestionJob

router = APIRouter()


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_job_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> IngestionJobResponse:
    """Alias for ingestion job status."""
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
