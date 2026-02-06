"""Match candidate endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.case_service import CaseService

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class UpdateMatchRequest(BaseModel):
    """Request to update a match candidate."""

    status: str  # candidate, reviewing, confirmed, dismissed


class MatchResponse(BaseModel):
    """Match candidate response."""

    id: str
    patent_id: str
    product_id: str | None
    company_id: str | None
    product_name: str | None
    company_name: str | None
    score_total: float | None
    score_coverage: float | None
    score_evidence_quality: float | None
    score_blackbox_penalty: float | None
    score_legal_status: float | None
    logic_version: str | None
    analysis_job_id: str | None
    status: str
    created_at: str
    updated_at: str


class MatchListResponse(BaseModel):
    """Match list response."""

    matches: list[MatchResponse]
    total: int
    page: int
    per_page: int


def _match_to_response(m) -> MatchResponse:
    """Convert MatchCandidate model to response."""
    return MatchResponse(
        id=str(m.id),
        patent_id=str(m.patent_id),
        product_id=str(m.product_id) if m.product_id else None,
        company_id=str(m.company_id) if m.company_id else None,
        product_name=m.product.name if m.product else None,
        company_name=m.company.name if m.company else None,
        score_total=m.score_total,
        score_coverage=m.score_coverage,
        score_evidence_quality=m.score_evidence_quality,
        score_blackbox_penalty=m.score_blackbox_penalty,
        score_legal_status=m.score_legal_status,
        logic_version=m.logic_version,
        analysis_job_id=str(m.analysis_job_id) if m.analysis_job_id else None,
        status=m.status,
        created_at=m.created_at.isoformat(),
        updated_at=m.updated_at.isoformat(),
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=MatchListResponse)
def list_matches(
    db: Annotated[Session, Depends(get_db)],
    patent_id: str | None = None,
    product_id: str | None = None,
    company_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> MatchListResponse:
    """List match candidates with optional filters."""
    service = CaseService(db)

    try:
        p_uuid = uuid.UUID(patent_id) if patent_id else None
        pr_uuid = uuid.UUID(product_id) if product_id else None
        c_uuid = uuid.UUID(company_id) if company_id else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid UUID format") from e

    matches, total = service.list_matches(
        patent_id=p_uuid,
        product_id=pr_uuid,
        company_id=c_uuid,
        status=status,
        page=page,
        per_page=per_page,
    )

    return MatchListResponse(
        matches=[_match_to_response(m) for m in matches],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> MatchResponse:
    """Get match candidate details."""
    try:
        match_uuid = uuid.UUID(match_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid match ID format") from e

    service = CaseService(db)
    match = service.get_match(match_uuid)
    if not match:
        raise HTTPException(status_code=404, detail="Match candidate not found")

    return _match_to_response(match)


@router.patch("/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: str,
    request: UpdateMatchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MatchResponse:
    """Update match candidate status."""
    try:
        match_uuid = uuid.UUID(match_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid match ID format") from e

    service = CaseService(db)
    try:
        match = service.update_match_status(match_uuid, status=request.status)
        if not match:
            raise HTTPException(status_code=404, detail="Match candidate not found")
        db.commit()
        return _match_to_response(match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
