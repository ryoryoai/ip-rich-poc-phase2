"""Link endpoints for company/product/patent relationships."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import CompanyProductLink, PatentCompanyLink, Company, Product, Document

router = APIRouter()


class CompanyProductLinkRequest(BaseModel):
    company_id: str
    product_id: str
    role: str = Field(..., min_length=1)
    link_type: str = Field(..., min_length=1)
    confidence_score: float | None = None
    evidence_json: dict | None = None


class PatentCompanyLinkRequest(BaseModel):
    company_id: str
    document_id: str | None = None
    patent_ref: str | None = None
    role: str = Field(..., min_length=1)
    link_type: str = Field(..., min_length=1)
    confidence_score: float | None = None
    evidence_json: dict | None = None


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reviewed_by: str | None = None
    note: str | None = None


@router.post("/company-product")
def create_company_product_link(
    request: CompanyProductLinkRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create a company-product link."""
    if request.link_type not in {"deterministic", "probabilistic"}:
        raise HTTPException(status_code=400, detail="Invalid link_type")
    try:
        company_uuid = uuid.UUID(request.company_id)
        product_uuid = uuid.UUID(request.product_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid UUID") from exc

    if not db.query(Company).filter(Company.id == company_uuid).first():
        raise HTTPException(status_code=404, detail="Company not found")

    if not db.query(Product).filter(Product.id == product_uuid).first():
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(CompanyProductLink)
        .filter(
            CompanyProductLink.company_id == company_uuid,
            CompanyProductLink.product_id == product_uuid,
            CompanyProductLink.role == request.role,
        )
        .first()
    )
    if existing:
        return {"link_id": str(existing.id), "existing": True}

    link = CompanyProductLink(
        company_id=company_uuid,
        product_id=product_uuid,
        role=request.role,
        link_type=request.link_type,
        confidence_score=request.confidence_score,
        review_status="approved" if request.link_type == "deterministic" else "pending",
        evidence_json=request.evidence_json,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {"link_id": str(link.id), "existing": False}


@router.post("/patent-company")
def create_patent_company_link(
    request: PatentCompanyLinkRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create a patent-company link."""
    if request.link_type not in {"deterministic", "probabilistic"}:
        raise HTTPException(status_code=400, detail="Invalid link_type")
    try:
        company_uuid = uuid.UUID(request.company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid company ID") from exc

    document_uuid = None
    if request.document_id:
        try:
            document_uuid = uuid.UUID(request.document_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid document ID") from exc

    if not db.query(Company).filter(Company.id == company_uuid).first():
        raise HTTPException(status_code=404, detail="Company not found")

    if document_uuid:
        if not db.query(Document).filter(Document.id == document_uuid).first():
            raise HTTPException(status_code=404, detail="Document not found")

    if not document_uuid and not request.patent_ref:
        raise HTTPException(status_code=400, detail="document_id or patent_ref is required")

    existing = (
        db.query(PatentCompanyLink)
        .filter(
            PatentCompanyLink.company_id == company_uuid,
            PatentCompanyLink.document_id == document_uuid,
            PatentCompanyLink.patent_ref == request.patent_ref,
            PatentCompanyLink.role == request.role,
        )
        .first()
    )
    if existing:
        return {"link_id": str(existing.id), "existing": True}

    link = PatentCompanyLink(
        company_id=company_uuid,
        document_id=document_uuid,
        patent_ref=request.patent_ref,
        role=request.role,
        link_type=request.link_type,
        confidence_score=request.confidence_score,
        review_status="approved" if request.link_type == "deterministic" else "pending",
        evidence_json=request.evidence_json,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {"link_id": str(link.id), "existing": False}


@router.get("/review-queue")
def review_queue(
    db: Annotated[Session, Depends(get_db)],
    link_type: str = "probabilistic",
    review_status: str = "pending",
    limit: int = 50,
) -> dict:
    """Return links that require review (probabilistic by default)."""
    patent_links = (
        db.query(PatentCompanyLink)
        .filter(
            PatentCompanyLink.link_type == link_type,
            PatentCompanyLink.review_status == review_status,
        )
        .order_by(PatentCompanyLink.created_at.desc())
        .limit(limit)
        .all()
    )
    company_product_links = (
        db.query(CompanyProductLink)
        .filter(
            CompanyProductLink.link_type == link_type,
            CompanyProductLink.review_status == review_status,
        )
        .order_by(CompanyProductLink.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "patent_company_links": [
            {
                "link_id": str(link.id),
                "company_id": str(link.company_id),
                "document_id": str(link.document_id) if link.document_id else None,
                "patent_ref": link.patent_ref,
                "role": link.role,
                "link_type": link.link_type,
                "confidence_score": link.confidence_score,
                "review_status": link.review_status,
            }
            for link in patent_links
        ],
        "company_product_links": [
            {
                "link_id": str(link.id),
                "company_id": str(link.company_id),
                "product_id": str(link.product_id),
                "role": link.role,
                "link_type": link.link_type,
                "confidence_score": link.confidence_score,
                "review_status": link.review_status,
            }
            for link in company_product_links
        ],
    }


@router.post("/company-product/{link_id}/review")
def review_company_product_link(
    link_id: str,
    request: ReviewRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Approve or reject a company-product link."""
    try:
        link_uuid = uuid.UUID(link_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid link ID") from exc

    link = db.query(CompanyProductLink).filter(CompanyProductLink.id == link_uuid).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.review_status = "approved" if request.decision == "approve" else "rejected"
    link.review_note = request.note
    link.verified_by = request.reviewed_by
    link.verified_at = datetime.now(timezone.utc)
    if request.decision == "approve":
        link.link_type = "deterministic"

    db.commit()
    db.refresh(link)

    return {
        "link_id": str(link.id),
        "review_status": link.review_status,
        "link_type": link.link_type,
    }


@router.post("/patent-company/{link_id}/review")
def review_patent_company_link(
    link_id: str,
    request: ReviewRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Approve or reject a patent-company link."""
    try:
        link_uuid = uuid.UUID(link_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid link ID") from exc

    link = db.query(PatentCompanyLink).filter(PatentCompanyLink.id == link_uuid).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.review_status = "approved" if request.decision == "approve" else "rejected"
    link.review_note = request.note
    link.verified_by = request.reviewed_by
    link.verified_at = datetime.now(timezone.utc)
    if request.decision == "approve":
        link.link_type = "deterministic"

    db.commit()
    db.refresh(link)

    return {
        "link_id": str(link.id),
        "review_status": link.review_status,
        "link_type": link.link_type,
    }
