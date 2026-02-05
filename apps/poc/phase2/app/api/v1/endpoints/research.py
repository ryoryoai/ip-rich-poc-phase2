"""Deep Research endpoints for patent investigation."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import AnalysisJob
from app.llm.deep_research import DeepResearchJobManager

router = APIRouter()


class StartResearchRequest(BaseModel):
    """Request to start Deep Research."""

    patent_number: str
    claim_text: str | None = None
    company_name: str | None = None
    product_name: str | None = None


class StartResearchResponse(BaseModel):
    """Response after starting Deep Research."""

    job_id: str
    status: str
    existing: bool = False


async def run_deep_research(
    job_id: uuid.UUID,
    patent_number: str,
    claim_text: str | None,
    db_url: str,
):
    """Background task to run Deep Research."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SQLSession

    # Create a new session for the background task
    engine = create_engine(db_url)
    with SQLSession(engine) as db:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return

        try:
            job.status = "researching"
            job.started_at = datetime.now(timezone.utc)
            db.commit()

            # Run Deep Research
            manager = DeepResearchJobManager()
            result = await manager.start_research(
                str(job_id),
                patent_number,
                claim_text,
            )

            # Update job with results
            job.research_results = result.get("result", {})

            if result["status"] == "completed":
                job.status = "completed"
            else:
                job.status = "failed"
                job.error_message = result.get("error", "Unknown error")

            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()


@router.post("/start", response_model=StartResearchResponse)
def start_research(
    request: StartResearchRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> StartResearchResponse:
    """Start a new Deep Research job for patent investigation."""
    from app.core.config import settings

    # Check for existing completed job with same patent number
    existing_job = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.patent_id == request.patent_number,
            AnalysisJob.status == "completed",
        )
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )

    if existing_job:
        return StartResearchResponse(
            job_id=str(existing_job.id),
            status=existing_job.status,
            existing=True,
        )

    # Create new job
    job = AnalysisJob(
        patent_id=request.patent_number,
        claim_text=request.claim_text,
        company_name=request.company_name,
        product_name=request.product_name,
        pipeline="research",  # Special pipeline for Deep Research
        status="pending",
        search_type="deep_research",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background task
    background_tasks.add_task(
        run_deep_research,
        job.id,
        request.patent_number,
        request.claim_text,
        settings.database_url,
    )

    return StartResearchResponse(
        job_id=str(job.id),
        status="pending",
        existing=False,
    )


@router.get("/{job_id}")
def get_research_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get the status and results of a Deep Research job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_uuid).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": str(job.id),
        "status": job.status,
        "patent_id": job.patent_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "research_results": job.research_results,
    }
