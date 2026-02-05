"""Patent endpoints."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import (
    Document,
    Claim,
    DocumentText,
    Patent,
    PatentVersion,
    PatentClaim,
    PatentSpecSection,
)

router = APIRouter()


class ResolveResponse(BaseModel):
    """Response for patent number resolution."""

    country: str
    doc_number: str
    kind: str | None
    normalized: str


class ClaimResponse(BaseModel):
    """Response for claim retrieval."""

    patent_id: str
    claim_no: int
    claim_text: str
    text_raw: str | None = None
    text_norm: str | None = None


class ClaimListResponse(BaseModel):
    """Response for all claims."""

    patent_id: str
    version_id: str | None = None
    claims: list[ClaimResponse]


class DocumentTextResponse(BaseModel):
    """Response for document text retrieval."""

    patent_id: str
    text_type: str
    text: str
    language: str | None
    source: str | None
    updated_at: str | None


# Note: keep response compatible with existing clients (claim_text remains).


class SpecSection(BaseModel):
    section_type: str
    order: int
    text_raw: str
    text_norm: str | None = None


class SpecResponse(BaseModel):
    patent_id: str
    version_id: str | None
    sections: list[SpecSection]


class VersionItem(BaseModel):
    version_id: str
    publication_type: str
    issue_date: str | None
    source_type: str
    content_hash: str | None
    is_latest: bool


class VersionsResponse(BaseModel):
    patent_id: str
    versions: list[VersionItem]


def normalize_patent_number(input_str: str) -> ResolveResponse:
    """
    Normalize various Japanese patent number formats.

    Supported formats:
    - 特許第1234567号
    - JP1234567B2
    - 1234567
    - 特願2020-123456
    """
    input_str = input_str.strip()

    # Pattern: 特許第1234567号
    match = re.match(r"特許第(\d+)号", input_str)
    if match:
        return ResolveResponse(
            country="JP",
            doc_number=match.group(1),
            kind="B2",
            normalized=f"JP{match.group(1)}B2",
        )

    # Pattern: JP1234567B2
    match = re.match(r"JP(\d+)([A-Z]\d?)?", input_str, re.IGNORECASE)
    if match:
        doc_num = match.group(1)
        kind = match.group(2) or "B2"
        return ResolveResponse(
            country="JP",
            doc_number=doc_num,
            kind=kind.upper(),
            normalized=f"JP{doc_num}{kind.upper()}",
        )

    # Pattern: Just numbers
    match = re.match(r"^(\d{6,8})$", input_str)
    if match:
        return ResolveResponse(
            country="JP",
            doc_number=match.group(1),
            kind="B2",
            normalized=f"JP{match.group(1)}B2",
        )

    # Pattern: 特願2020-123456 (application number)
    match = re.match(r"特願(\d{4})-(\d+)", input_str)
    if match:
        year = match.group(1)
        num = match.group(2)
        return ResolveResponse(
            country="JP",
            doc_number=f"{year}{num}",
            kind="A",
            normalized=f"JP{year}{num}A",
        )

    raise HTTPException(status_code=400, detail=f"Cannot parse patent number: {input_str}")


def _infer_number_type(input_str: str, resolved: ResolveResponse) -> str:
    if "特願" in input_str:
        return "application"
    if resolved.kind and resolved.kind.upper().startswith("B"):
        return "registration"
    if resolved.kind and resolved.kind.upper().startswith("A"):
        return "publication"
    return "publication"


def _resolve_internal_patent(
    db: Session, input_str: str
) -> tuple[Patent | None, ResolveResponse, str]:
    resolved = normalize_patent_number(input_str)
    number_type = _infer_number_type(input_str, resolved)

    patent = None
    if number_type == "application":
        patent = (
            db.query(Patent)
            .filter(
                Patent.jurisdiction == resolved.country,
                Patent.application_no == resolved.doc_number,
            )
            .first()
        )
    elif number_type == "registration":
        patent = (
            db.query(Patent)
            .filter(
                Patent.jurisdiction == resolved.country,
                Patent.registration_no == resolved.doc_number,
            )
            .first()
        )
    else:
        patent = (
            db.query(Patent)
            .filter(
                Patent.jurisdiction == resolved.country,
                Patent.publication_no == resolved.doc_number,
            )
            .first()
        )

    if not patent:
        patent = (
            db.query(Patent)
            .filter(
                Patent.jurisdiction == resolved.country,
                or_(
                    Patent.application_no == resolved.doc_number,
                    Patent.publication_no == resolved.doc_number,
                    Patent.registration_no == resolved.doc_number,
                ),
            )
            .first()
        )

    return patent, resolved, number_type


def _latest_version(
    db: Session, patent: Patent, publication_type: str | None
) -> PatentVersion | None:
    query = db.query(PatentVersion).filter(
        PatentVersion.internal_patent_id == patent.internal_patent_id
    )
    if publication_type:
        query = query.filter(PatentVersion.publication_type == publication_type)

    query = query.order_by(
        desc(PatentVersion.is_latest),
        desc(PatentVersion.issue_date).nulls_last(),
        desc(PatentVersion.created_at),
    )
    return query.first()


@router.get("/resolve")
async def resolve_patent_number(
    input: Annotated[str, Query(description="Patent number in various formats")],
) -> ResolveResponse:
    """Resolve and normalize a patent number."""
    return normalize_patent_number(input)


@router.get("/{patent_id}/claims/{claim_no}")
async def get_claim(
    patent_id: str,
    claim_no: int,
    db: Annotated[Session, Depends(get_db)],
) -> ClaimResponse:
    """Get a specific claim from a patent document."""
    patent, resolved, number_type = _resolve_internal_patent(db, patent_id)

    publication_type = None
    if number_type == "registration":
        publication_type = "grant"
    elif number_type == "publication":
        publication_type = "publication"

    if patent:
        version = _latest_version(db, patent, publication_type)
        if version:
            claim = (
                db.query(PatentClaim)
                .filter(
                    PatentClaim.version_id == version.version_id,
                    PatentClaim.claim_no == claim_no,
                )
                .first()
            )
            if claim:
                return ClaimResponse(
                    patent_id=resolved.normalized,
                    claim_no=claim_no,
                    claim_text=claim.text_norm or claim.text_raw,
                    text_raw=claim.text_raw,
                    text_norm=claim.text_norm,
                )

    # Find document
    document = (
        db.query(Document)
        .filter(
            Document.country == resolved.country,
            Document.doc_number == resolved.doc_number,
            Document.kind == resolved.kind,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail=f"Patent {patent_id} not found")

    # Find claim
    claim = (
        db.query(Claim)
        .filter(
            Claim.document_id == document.id,
            Claim.claim_no == claim_no,
        )
        .first()
    )

    if not claim:
        raise HTTPException(
            status_code=404, detail=f"Claim {claim_no} not found for patent {patent_id}"
        )

    return ClaimResponse(
        patent_id=resolved.normalized,
        claim_no=claim_no,
        claim_text=claim.claim_text,
        text_raw=claim.claim_text,
        text_norm=None,
    )


@router.get("/{patent_id}/claims", response_model=ClaimListResponse)
async def get_claims(
    patent_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ClaimListResponse:
    """Get all claims for a patent document."""
    patent, resolved, number_type = _resolve_internal_patent(db, patent_id)

    publication_type = None
    if number_type == "registration":
        publication_type = "grant"
    elif number_type == "publication":
        publication_type = "publication"

    if patent:
        version = _latest_version(db, patent, publication_type)
        if version:
            claims = (
                db.query(PatentClaim)
                .filter(PatentClaim.version_id == version.version_id)
                .order_by(PatentClaim.claim_no.asc())
                .all()
            )
            return ClaimListResponse(
                patent_id=resolved.normalized,
                version_id=str(version.version_id),
                claims=[
                    ClaimResponse(
                        patent_id=resolved.normalized,
                        claim_no=claim.claim_no,
                        claim_text=claim.text_norm or claim.text_raw,
                        text_raw=claim.text_raw,
                        text_norm=claim.text_norm,
                    )
                    for claim in claims
                ],
            )
    document = (
        db.query(Document)
        .filter(
            Document.country == resolved.country,
            Document.doc_number == resolved.doc_number,
            Document.kind == resolved.kind,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail=f"Patent {patent_id} not found")

    claims = (
        db.query(Claim)
        .filter(Claim.document_id == document.id)
        .order_by(Claim.claim_no.asc())
        .all()
    )

    return ClaimListResponse(
        patent_id=resolved.normalized,
        version_id=None,
        claims=[
            ClaimResponse(
                patent_id=resolved.normalized,
                claim_no=claim.claim_no,
                claim_text=claim.claim_text,
                text_raw=claim.claim_text,
                text_norm=None,
            )
            for claim in claims
        ],
    )


@router.get("/{patent_id}/texts/{text_type}", response_model=DocumentTextResponse)
async def get_document_text(
    patent_id: str,
    text_type: str,
    db: Annotated[Session, Depends(get_db)],
    language: Annotated[str | None, Query()] = None,
) -> DocumentTextResponse:
    """Get a long-form document text (e.g., specification)."""
    resolved = normalize_patent_number(patent_id)
    document = (
        db.query(Document)
        .filter(
            Document.country == resolved.country,
            Document.doc_number == resolved.doc_number,
            Document.kind == resolved.kind,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail=f"Patent {patent_id} not found")

    query = (
        db.query(DocumentText)
        .filter(
            DocumentText.document_id == document.id,
            DocumentText.text_type == text_type,
            DocumentText.is_current.is_(True),
        )
        .order_by(DocumentText.updated_at.desc().nullslast(), DocumentText.created_at.desc())
    )
    if language:
        query = query.filter(DocumentText.language == language)

    text = query.first()
    if not text:
        raise HTTPException(status_code=404, detail=f"No {text_type} text found for {patent_id}")

    return DocumentTextResponse(
        patent_id=resolved.normalized,
        text_type=text.text_type,
        text=text.text,
        language=text.language,
        source=text.source,
        updated_at=text.updated_at.isoformat() if text.updated_at else None,
    )


@router.get("/{patent_id}/spec", response_model=SpecResponse)
async def get_spec(
    patent_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> SpecResponse:
    """Get specification sections for a patent (latest version if available)."""
    patent, resolved, number_type = _resolve_internal_patent(db, patent_id)

    publication_type = None
    if number_type == "registration":
        publication_type = "grant"
    elif number_type == "publication":
        publication_type = "publication"

    if patent:
        version = _latest_version(db, patent, publication_type)
        if version:
            sections = (
                db.query(PatentSpecSection)
                .filter(PatentSpecSection.version_id == version.version_id)
                .order_by(PatentSpecSection.section_type, PatentSpecSection.order_no)
                .all()
            )
            return SpecResponse(
                patent_id=resolved.normalized,
                version_id=str(version.version_id),
                sections=[
                    SpecSection(
                        section_type=s.section_type,
                        order=s.order_no,
                        text_raw=s.text_raw,
                        text_norm=s.text_norm,
                    )
                    for s in sections
                ],
            )

    # Fallback to legacy document text
    document = (
        db.query(Document)
        .filter(
            Document.country == resolved.country,
            Document.doc_number == resolved.doc_number,
            Document.kind == resolved.kind,
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail=f"Patent {patent_id} not found")

    text = (
        db.query(DocumentText)
        .filter(
            DocumentText.document_id == document.id,
            DocumentText.text_type == "specification",
            DocumentText.is_current.is_(True),
        )
        .first()
    )
    sections: list[SpecSection] = []
    if text:
        sections.append(
            SpecSection(
                section_type="full",
                order=1,
                text_raw=text.text,
                text_norm=None,
            )
        )
    return SpecResponse(
        patent_id=resolved.normalized,
        version_id=None,
        sections=sections,
    )


@router.get("/{patent_id}/versions", response_model=VersionsResponse)
async def get_versions(
    patent_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> VersionsResponse:
    """Get all versions for a patent."""
    patent, resolved, _ = _resolve_internal_patent(db, patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail=f"Patent {patent_id} not found")

    versions = (
        db.query(PatentVersion)
        .filter(PatentVersion.internal_patent_id == patent.internal_patent_id)
        .order_by(desc(PatentVersion.issue_date).nulls_last(), desc(PatentVersion.created_at))
        .all()
    )
    return VersionsResponse(
        patent_id=resolved.normalized,
        versions=[
            VersionItem(
                version_id=str(v.version_id),
                publication_type=v.publication_type,
                issue_date=v.issue_date.isoformat() if v.issue_date else None,
                source_type=v.source_type,
                content_hash=v.content_hash,
                is_latest=v.is_latest,
            )
            for v in versions
        ],
    )
