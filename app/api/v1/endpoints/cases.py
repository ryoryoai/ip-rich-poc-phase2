"""Investigation case management endpoints."""

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


class CreateCaseRequest(BaseModel):
    """Request to create a new investigation case."""

    title: str
    description: str | None = None
    patent_id: str | None = None
    assignee_id: str | None = None


class UpdateCaseRequest(BaseModel):
    """Request to update an investigation case."""

    title: str | None = None
    description: str | None = None
    status: str | None = None
    assignee_id: str | None = None


class AddTargetRequest(BaseModel):
    """Request to add a target to a case."""

    target_type: str  # 'patent', 'product', 'company'
    target_id: str


class AddCaseMatchRequest(BaseModel):
    """Request to link a match candidate to a case."""

    match_candidate_id: str
    reviewer_note: str | None = None


class CaseResponse(BaseModel):
    """Case response."""

    id: str
    title: str
    description: str | None
    status: str
    assignee_id: str | None
    patent_id: str | None
    created_at: str
    updated_at: str


class CaseListResponse(BaseModel):
    """Case list response."""

    cases: list[CaseResponse]
    total: int
    page: int
    per_page: int


class TargetResponse(BaseModel):
    """Case target response."""

    id: str
    target_type: str
    target_id: str
    created_at: str


class CaseMatchResponse(BaseModel):
    """Case match response."""

    id: str
    match_candidate_id: str
    reviewer_note: str | None
    score_total: float | None
    product_name: str | None
    company_name: str | None
    status: str | None
    created_at: str


class CaseDetailResponse(BaseModel):
    """Case detail response including targets and matches."""

    case: CaseResponse
    targets: list[TargetResponse]
    matches: list[CaseMatchResponse]


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=CaseResponse)
def create_case(
    request: CreateCaseRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CaseResponse:
    """Create a new investigation case."""
    service = CaseService(db)
    try:
        patent_uuid = uuid.UUID(request.patent_id) if request.patent_id else None
        assignee_uuid = uuid.UUID(request.assignee_id) if request.assignee_id else None

        case = service.create_case(
            title=request.title,
            description=request.description,
            patent_id=patent_uuid,
            assignee_id=assignee_uuid,
        )
        db.commit()

        return CaseResponse(
            id=str(case.id),
            title=case.title,
            description=case.description,
            status=case.status,
            assignee_id=str(case.assignee_id) if case.assignee_id else None,
            patent_id=str(case.patent_id) if case.patent_id else None,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=CaseListResponse)
def list_cases(
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> CaseListResponse:
    """List investigation cases with optional status filter."""
    service = CaseService(db)
    cases, total = service.list_cases(status=status, page=page, per_page=per_page)

    return CaseListResponse(
        cases=[
            CaseResponse(
                id=str(c.id),
                title=c.title,
                description=c.description,
                status=c.status,
                assignee_id=str(c.assignee_id) if c.assignee_id else None,
                patent_id=str(c.patent_id) if c.patent_id else None,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in cases
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> CaseDetailResponse:
    """Get case details including targets and matches."""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid case ID format") from e

    service = CaseService(db)
    case = service.get_case(case_uuid)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    targets = service.get_targets(case_uuid)
    case_matches = service.get_case_matches(case_uuid)

    return CaseDetailResponse(
        case=CaseResponse(
            id=str(case.id),
            title=case.title,
            description=case.description,
            status=case.status,
            assignee_id=str(case.assignee_id) if case.assignee_id else None,
            patent_id=str(case.patent_id) if case.patent_id else None,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
        ),
        targets=[
            TargetResponse(
                id=str(t.id),
                target_type=t.target_type,
                target_id=str(t.target_id),
                created_at=t.created_at.isoformat(),
            )
            for t in targets
        ],
        matches=[
            CaseMatchResponse(
                id=str(cm.id),
                match_candidate_id=str(cm.match_candidate_id),
                reviewer_note=cm.reviewer_note,
                score_total=cm.match_candidate.score_total if cm.match_candidate else None,
                product_name=(
                    cm.match_candidate.product.name
                    if cm.match_candidate and cm.match_candidate.product
                    else None
                ),
                company_name=(
                    cm.match_candidate.company.name
                    if cm.match_candidate and cm.match_candidate.company
                    else None
                ),
                status=cm.match_candidate.status if cm.match_candidate else None,
                created_at=cm.created_at.isoformat(),
            )
            for cm in case_matches
        ],
    )


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    request: UpdateCaseRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CaseResponse:
    """Update case fields (title, description, status, assignee)."""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid case ID format") from e

    service = CaseService(db)
    try:
        assignee_uuid = uuid.UUID(request.assignee_id) if request.assignee_id else None
        case = service.update_case(
            case_uuid,
            title=request.title,
            description=request.description,
            status=request.status,
            assignee_id=assignee_uuid,
        )
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        db.commit()

        return CaseResponse(
            id=str(case.id),
            title=case.title,
            description=case.description,
            status=case.status,
            assignee_id=str(case.assignee_id) if case.assignee_id else None,
            patent_id=str(case.patent_id) if case.patent_id else None,
            created_at=case.created_at.isoformat(),
            updated_at=case.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{case_id}/targets", response_model=TargetResponse)
def add_target(
    case_id: str,
    request: AddTargetRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TargetResponse:
    """Add a target (patent/product/company) to a case."""
    try:
        case_uuid = uuid.UUID(case_id)
        target_uuid = uuid.UUID(request.target_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid UUID format") from e

    service = CaseService(db)
    case = service.get_case(case_uuid)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        target = service.add_target(
            case_uuid,
            target_type=request.target_type,
            target_id=target_uuid,
        )
        db.commit()

        return TargetResponse(
            id=str(target.id),
            target_type=target.target_type,
            target_id=str(target.target_id),
            created_at=target.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{case_id}/matches", response_model=list[CaseMatchResponse])
def get_case_matches(
    case_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> list[CaseMatchResponse]:
    """Get all match candidates linked to a case."""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid case ID format") from e

    service = CaseService(db)
    case = service.get_case(case_uuid)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case_matches = service.get_case_matches(case_uuid)
    return [
        CaseMatchResponse(
            id=str(cm.id),
            match_candidate_id=str(cm.match_candidate_id),
            reviewer_note=cm.reviewer_note,
            score_total=cm.match_candidate.score_total if cm.match_candidate else None,
            product_name=(
                cm.match_candidate.product.name
                if cm.match_candidate and cm.match_candidate.product
                else None
            ),
            company_name=(
                cm.match_candidate.company.name
                if cm.match_candidate and cm.match_candidate.company
                else None
            ),
            status=cm.match_candidate.status if cm.match_candidate else None,
            created_at=cm.created_at.isoformat(),
        )
        for cm in case_matches
    ]


@router.post("/{case_id}/matches", response_model=CaseMatchResponse)
def add_case_match(
    case_id: str,
    request: AddCaseMatchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CaseMatchResponse:
    """Link a match candidate to a case."""
    try:
        case_uuid = uuid.UUID(case_id)
        match_uuid = uuid.UUID(request.match_candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid UUID format") from e

    service = CaseService(db)
    case = service.get_case(case_uuid)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    match = service.get_match(match_uuid)
    if not match:
        raise HTTPException(status_code=404, detail="Match candidate not found")

    try:
        cm = service.add_case_match(
            case_uuid,
            match_uuid,
            reviewer_note=request.reviewer_note,
        )
        db.commit()

        return CaseMatchResponse(
            id=str(cm.id),
            match_candidate_id=str(cm.match_candidate_id),
            reviewer_note=cm.reviewer_note,
            score_total=match.score_total,
            product_name=match.product.name if match.product else None,
            company_name=match.company.name if match.company else None,
            status=match.status,
            created_at=cm.created_at.isoformat(),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
