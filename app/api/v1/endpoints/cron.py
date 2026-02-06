"""Cron endpoints for scheduled tasks."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import get_logger, settings

router = APIRouter()
logger = get_logger(__name__)

MAX_CONCURRENT_JOBS = settings.max_concurrent_jobs


def verify_cron_secret(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Verify the cron secret from Authorization header."""
    if not settings.cron_secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not configured")

    expected = f"Bearer {settings.cron_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid cron secret")


@router.post("/batch-analyze")
@router.get("/batch-analyze")  # Support both GET and POST for cron
def batch_analyze(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(verify_cron_secret)],
) -> dict:
    """
    Batch analysis cron job (Phase1 check-and-do equivalent).

    1. Check running Deep Research jobs for completion
    2. Start pending jobs (respecting concurrency limit)
    3. Handle retries for failed jobs

    Called by Vercel Cron every 6 hours.
    """
    from app.db.models import AnalysisJob
    from app.services import AnalysisService

    results = {
        "checked_running": 0,
        "completed": 0,
        "started": 0,
        "retried": 0,
        "errors": [],
    }

    # 1. Check currently running jobs
    running_jobs = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.status.in_(["researching", "analyzing", "running"]))  # running = legacy
        .all()
    )
    results["checked_running"] = len(running_jobs)

    for job in running_jobs:
        # If job has been running for more than 30 minutes, mark as failed
        started_at = job.started_at or job.queued_at
        if started_at:
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            if elapsed > 1800:  # 30 minutes
                logger.warning(
                    f"Job {job.id} timed out after {elapsed}s",
                    job_id=str(job.id),
                )
                job.status = "failed"
                job.error_message = "Job timed out"
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
                results["errors"].append({
                    "job_id": str(job.id),
                    "error": "timeout",
                })

    # 2. Count active jobs for concurrency check
    active_count = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.status.in_(["researching", "analyzing", "running"]))  # running = legacy
        .count()
    )

    slots_available = MAX_CONCURRENT_JOBS - active_count
    logger.info(
        f"Batch analyze: {active_count} active jobs, {slots_available} slots available"
    )

    if slots_available <= 0:
        return {**results, "message": "Max concurrent jobs reached"}

    # 3. Find pending jobs (prioritized)
    pending_jobs = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.status == "pending",
            or_(
                AnalysisJob.scheduled_for.is_(None),
                AnalysisJob.scheduled_for <= datetime.now(timezone.utc),
            ),
        )
        .order_by(
            AnalysisJob.priority.desc(),
            AnalysisJob.created_at.asc(),
        )
        .limit(slots_available)
        .all()
    )

    service = AnalysisService(db)

    for job in pending_jobs:
        try:
            logger.info(f"Starting job {job.id}", job_id=str(job.id))
            job.status = "analyzing"
            job.started_at = datetime.now(timezone.utc)
            job.queued_at = datetime.now(timezone.utc)
            job.completed_at = None
            job.current_stage = None
            db.commit()

            service.run_job(job.id)
            db.commit()
            results["started"] += 1

            if job.status == "completed":
                results["completed"] += 1

        except Exception as e:
            logger.exception(f"Job {job.id} failed", job_id=str(job.id))
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            results["errors"].append({
                "job_id": str(job.id),
                "error": str(e),
            })

    # 4. Handle retries for failed jobs
    failed_jobs = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.status == "failed",
            AnalysisJob.retry_count < AnalysisJob.max_retries,
        )
        .limit(2)  # Limit retries per batch
        .all()
    )

    for job in failed_jobs:
        try:
            logger.info(
                f"Retrying job {job.id} (attempt {job.retry_count + 1})",
                job_id=str(job.id),
            )
            job.status = "pending"
            job.retry_count += 1
            job.error_message = None
            db.commit()
            results["retried"] += 1
        except Exception as e:
            logger.exception(f"Retry setup failed for job {job.id}")
            results["errors"].append({
                "job_id": str(job.id),
                "error": f"retry setup failed: {e}",
            })

    return results


@router.post("/poll-patents")
@router.get("/poll-patents")  # Support both GET and POST for cron
def poll_patents(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(verify_cron_secret)],
) -> dict:
    """
    Poll patents for status changes.

    Scheduled job to check monitored patents for updates.
    Called by Vercel Cron daily at 9 AM.
    """
    from app.db.models import Document
    from app.llm.deep_research import DeepResearchProvider

    logger.info("Patent polling cron triggered")

    # Find patents that need monitoring
    # For now, just return status
    patent_count = db.query(Document).count()

    return {
        "status": "ok",
        "patents_in_system": patent_count,
        "message": "Patent polling completed",
    }


@router.post("/check-and-do")
@router.get("/check-and-do")  # Alias for Phase1 compatibility
def check_and_do(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(verify_cron_secret)],
) -> dict:
    """
    Alias for batch-analyze (Phase1 compatibility).

    Maintained for backward compatibility with existing cron configurations.
    """
    return batch_analyze(db, None)
