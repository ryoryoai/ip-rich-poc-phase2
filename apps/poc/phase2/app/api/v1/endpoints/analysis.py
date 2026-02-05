"""Analysis endpoints for patent infringement investigation."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import AnalysisService

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class StartAnalysisRequest(BaseModel):
    """Request to start a new analysis."""

    patent_id: str
    target_product: str | None = None
    company_id: str | None = None
    product_id: str | None = None
    pipeline: Literal["A", "B", "C", "full"] = "C"


class StartAnalysisResponse(BaseModel):
    """Response after starting an analysis."""

    job_id: str
    status: str
    patent_id: str
    pipeline: str


class JobStatusResponse(BaseModel):
    """Response for job status."""

    job_id: str
    status: str
    patent_id: str
    pipeline: str
    current_stage: str | None
    error_message: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None


class StageResultResponse(BaseModel):
    """Response for a single stage result."""

    stage: str
    output_data: dict | list | None  # list added for Phase1 compatibility
    llm_model: str | None
    tokens_input: int | None
    tokens_output: int | None
    latency_ms: int | None
    created_at: str


class JobResultsResponse(BaseModel):
    """Response for job results."""

    job_id: str
    status: str
    results: list[StageResultResponse]


class JobListItem(BaseModel):
    """Single job in the list."""

    id: str
    status: str
    patent_id: str
    pipeline: str
    created_at: str
    completed_at: str | None
    infringement_score: float | None


class JobListResponse(BaseModel):
    """Response for job list."""

    jobs: list[JobListItem]
    total: int
    page: int
    per_page: int


class RetryResponse(BaseModel):
    """Response for retry endpoint."""

    job_id: str
    status: str


# =============================================================================
# STATIC ROUTES (must be defined before dynamic routes)
# =============================================================================

@router.post("/start", response_model=StartAnalysisResponse)
def start_analysis(
    request: StartAnalysisRequest,
    db: Annotated[Session, Depends(get_db)],
) -> StartAnalysisResponse:
    """Start a new patent infringement analysis job."""
    service = AnalysisService(db)

    try:
        company_uuid = uuid.UUID(request.company_id) if request.company_id else None
        product_uuid = uuid.UUID(request.product_id) if request.product_id else None

        job = service.create_job(
            patent_id=request.patent_id,
            pipeline=request.pipeline,
            target_product=request.target_product,
            company_id=company_uuid,
            product_id=product_uuid,
        )
        db.commit()

        # Run the job synchronously
        job = service.run_job(job.id)
        db.commit()

        return StartAnalysisResponse(
            job_id=str(job.id),
            status=job.status,
            patent_id=job.patent_id,
            pipeline=job.pipeline,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/list", response_model=JobListResponse)
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    per_page: int = 20,
) -> JobListResponse:
    """List all analysis jobs with pagination."""
    from app.db.models import AnalysisJob

    try:
        # Calculate offset
        offset = (page - 1) * per_page

        # Query jobs
        query = db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc())
        total = query.count()
        jobs = query.offset(offset).limit(per_page).all()

        return JobListResponse(
            jobs=[
                JobListItem(
                    id=str(j.id),
                    status=j.status,
                    patent_id=j.patent_id,
                    pipeline=getattr(j, "pipeline", "C"),
                    created_at=j.created_at.isoformat() if j.created_at else "",
                    completed_at=j.completed_at.isoformat() if j.completed_at else None,
                    infringement_score=getattr(j, "infringement_score", None),
                )
                for j in jobs
            ],
            total=total,
            page=page,
            per_page=per_page,
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{traceback.format_exc()}")


@router.get("/prompts/list")
def list_prompts() -> list[dict]:
    """List all available prompts."""
    from app.llm import PromptManager

    pm = PromptManager()
    return pm.list_prompts()


# =============================================================================
# DYNAMIC ROUTES (must be defined after static routes)
# =============================================================================

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> JobStatusResponse:
    """Get the status of an analysis job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    service = AnalysisService(db)
    job = service.get_job(job_uuid)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        patent_id=job.patent_id,
        pipeline=job.pipeline,
        current_stage=job.current_stage,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else "",
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> JobResultsResponse:
    """Get the results of an analysis job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    service = AnalysisService(db)
    job = service.get_job(job_uuid)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Phase1 migrated data: results are stored in research_results/summary JSON fields
    if job.pipeline == "phase1":
        phase1_results = []

        # Add research_results as a stage
        if job.research_results:
            phase1_results.append(StageResultResponse(
                stage="deep_research",
                output_data=job.research_results,
                llm_model="openai-deep-research",
                tokens_input=None,
                tokens_output=None,
                latency_ms=None,
                created_at=job.created_at.isoformat() if job.created_at else "",
            ))

        # Add summary as a stage
        if job.summary:
            phase1_results.append(StageResultResponse(
                stage="case_summary",
                output_data=job.summary,
                llm_model=None,
                tokens_input=None,
                tokens_output=None,
                latency_ms=None,
                created_at=job.completed_at.isoformat() if job.completed_at else "",
            ))

        # Add requirements if available
        if job.requirements:
            phase1_results.append(StageResultResponse(
                stage="requirements_extraction",
                output_data=job.requirements,
                llm_model=None,
                tokens_input=None,
                tokens_output=None,
                latency_ms=None,
                created_at=job.created_at.isoformat() if job.created_at else "",
            ))

        # Add compliance_results if available
        if job.compliance_results:
            phase1_results.append(StageResultResponse(
                stage="compliance_check",
                output_data=job.compliance_results,
                llm_model=None,
                tokens_input=None,
                tokens_output=None,
                latency_ms=None,
                created_at=job.completed_at.isoformat() if job.completed_at else "",
            ))

        return JobResultsResponse(
            job_id=str(job.id),
            status=job.status,
            results=phase1_results,
        )

    # Phase2 data: results are in analysis_results table
    results = service.get_job_results(job_uuid)

    return JobResultsResponse(
        job_id=str(job.id),
        status=job.status,
        results=[
            StageResultResponse(
                stage=r.stage,
                output_data=r.output_data,
                llm_model=r.llm_model,
                tokens_input=r.tokens_input,
                tokens_output=r.tokens_output,
                latency_ms=r.latency_ms,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in results
        ],
    )


@router.post("/{job_id}/retry", response_model=RetryResponse)
def retry_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> RetryResponse:
    """Retry a failed analysis job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    service = AnalysisService(db)
    job = service.get_job(job_uuid)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

    # Reset job status
    job.status = "pending"
    job.error_message = None
    job.retry_count = (job.retry_count or 0) + 1
    db.commit()

    # Run the job
    try:
        job = service.run_job(job.id)
        db.commit()
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()

    return RetryResponse(
        job_id=str(job.id),
        status=job.status,
    )
