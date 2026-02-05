"""Collection job monitoring endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import CollectionJob, CollectionItem

router = APIRouter()


class CollectionItemResponse(BaseModel):
    item_id: str
    entity_type: str
    entity_id: str | None
    source_type: str | None
    source_ref: str | None
    status: str
    retry_count: int
    error_code: str | None
    error_detail: str | None


class CollectionJobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    priority: int
    retry_count: int
    max_retries: int
    error_code: str | None
    error_detail: str | None
    created_at: str | None
    started_at: str | None
    finished_at: str | None
    items: list[CollectionItemResponse]


@router.get("/jobs")
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
    limit: int = 20,
) -> dict:
    """List collection jobs."""
    query = db.query(CollectionJob)
    if status:
        query = query.filter(CollectionJob.status == status)
    jobs = query.order_by(CollectionJob.created_at.desc()).limit(limit).all()

    return {
        "jobs": [
            {
                "job_id": str(job.job_id),
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            }
            for job in jobs
        ]
    }


@router.get("/jobs/{job_id}", response_model=CollectionJobResponse)
def get_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> CollectionJobResponse:
    """Get collection job detail."""
    job = db.query(CollectionJob).filter(CollectionJob.job_id == job_id).first()
    if not job:
        return CollectionJobResponse(
            job_id=job_id,
            job_type="unknown",
            status="not_found",
            priority=0,
            retry_count=0,
            max_retries=0,
            error_code="not_found",
            error_detail="Job not found",
            created_at=None,
            started_at=None,
            finished_at=None,
            items=[],
        )

    items = (
        db.query(CollectionItem)
        .filter(CollectionItem.job_id == job.job_id)
        .order_by(CollectionItem.created_at.desc())
        .all()
    )

    return CollectionJobResponse(
        job_id=str(job.job_id),
        job_type=job.job_type,
        status=job.status,
        priority=job.priority,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        error_code=job.error_code,
        error_detail=job.error_detail,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        items=[
            CollectionItemResponse(
                item_id=str(item.item_id),
                entity_type=item.entity_type,
                entity_id=str(item.entity_id) if item.entity_id else None,
                source_type=item.source_type,
                source_ref=item.source_ref,
                status=item.status,
                retry_count=item.retry_count,
                error_code=item.error_code,
                error_detail=item.error_detail,
            )
            for item in items
        ],
    )


@router.get("/metrics")
def collection_metrics(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Aggregate counts for collection jobs/items."""
    job_counts = (
        db.query(CollectionJob.status, func.count(CollectionJob.job_id))
        .group_by(CollectionJob.status)
        .all()
    )
    item_counts = (
        db.query(CollectionItem.status, func.count(CollectionItem.item_id))
        .group_by(CollectionItem.status)
        .all()
    )

    return {
        "jobs": {status: count for status, count in job_counts},
        "items": {status: count for status, count in item_counts},
    }
