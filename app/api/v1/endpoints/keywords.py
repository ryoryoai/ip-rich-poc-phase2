"""Technical keyword endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import TechKeyword, Evidence
from app.services.normalization import normalize_keyword_term

router = APIRouter()


class KeywordCreateRequest(BaseModel):
    term: str = Field(..., min_length=1)
    language: str | None = "ja"
    synonyms: list[str] | None = None
    abbreviations: list[str] | None = None
    domain: str | None = None
    notes: str | None = None
    source_evidence_id: str | None = None


class KeywordResponse(BaseModel):
    keyword_id: str
    term: str
    language: str
    normalized_term: str | None
    existing: bool = False


@router.post("", response_model=KeywordResponse)
def create_keyword(
    request: KeywordCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> KeywordResponse:
    """Create a technical keyword entry (idempotent by normalized term + language)."""
    normalized = normalize_keyword_term(request.term)
    language = request.language or "ja"

    existing = (
        db.query(TechKeyword)
        .filter(
            TechKeyword.normalized_term == normalized,
            TechKeyword.language == language,
        )
        .first()
    )
    if existing:
        return KeywordResponse(
            keyword_id=str(existing.id),
            term=existing.term,
            language=existing.language,
            normalized_term=existing.normalized_term,
            existing=True,
        )

    evidence_uuid = None
    if request.source_evidence_id:
        try:
            evidence_uuid = uuid.UUID(request.source_evidence_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid evidence ID") from exc
        if not db.query(Evidence).filter(Evidence.id == evidence_uuid).first():
            raise HTTPException(status_code=404, detail="Evidence not found")

    keyword = TechKeyword(
        term=request.term,
        language=language,
        normalized_term=normalized,
        synonyms=request.synonyms,
        abbreviations=request.abbreviations,
        domain=request.domain,
        notes=request.notes,
        source_evidence_id=evidence_uuid,
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)

    return KeywordResponse(
        keyword_id=str(keyword.id),
        term=keyword.term,
        language=keyword.language,
        normalized_term=keyword.normalized_term,
        existing=False,
    )


@router.get("/search")
def search_keywords(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
    language: str | None = None,
) -> dict:
    """Search keywords by term."""
    if not q.strip():
        return {"results": []}

    normalized = normalize_keyword_term(q)
    query = db.query(TechKeyword)

    if language:
        query = query.filter(TechKeyword.language == language)

    results = (
        query.filter(
            or_(
                TechKeyword.term.ilike(f"%{q}%"),
                TechKeyword.normalized_term.ilike(f"%{normalized}%"),
            )
        )
        .limit(limit)
        .all()
    )

    return {
        "results": [
            {
                "keyword_id": str(item.id),
                "term": item.term,
                "language": item.language,
                "synonyms": item.synonyms or [],
                "abbreviations": item.abbreviations or [],
                "domain": item.domain,
            }
            for item in results
        ]
    }


@router.get("/{keyword_id}")
def get_keyword(
    keyword_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get a keyword entry."""
    try:
        keyword_uuid = uuid.UUID(keyword_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid keyword ID") from exc

    keyword = db.query(TechKeyword).filter(TechKeyword.id == keyword_uuid).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return {
        "keyword_id": str(keyword.id),
        "term": keyword.term,
        "language": keyword.language,
        "normalized_term": keyword.normalized_term,
        "synonyms": keyword.synonyms or [],
        "abbreviations": keyword.abbreviations or [],
        "domain": keyword.domain,
        "notes": keyword.notes,
        "source_evidence_id": str(keyword.source_evidence_id) if keyword.source_evidence_id else None,
    }
