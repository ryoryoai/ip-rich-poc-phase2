"""Company master data endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import (
    Company,
    CompanyAlias,
    CompanyIdentifier,
    CompanyEvidenceLink,
    Evidence,
)
from app.services.normalization import normalize_company_name

router = APIRouter()


class CompanyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    corporate_number: str | None = None
    country: str | None = None
    legal_type: str | None = None
    address_raw: str | None = None
    address_pref: str | None = None
    address_city: str | None = None
    status: str | None = None
    business_description: str | None = None
    primary_products: str | None = None
    market_regions: str | None = None
    is_listed: bool | None = None
    has_jp_entity: bool | None = None
    website_url: str | None = None
    contact_url: str | None = None
    aliases: list[str] | None = None


class CompanyResponse(BaseModel):
    company_id: str
    name: str
    corporate_number: str | None = None
    normalized_name: str | None = None
    identity_type: str | None = None
    identity_confidence: float | None = None
    existing: bool = False


class CompanyAliasRequest(BaseModel):
    alias: str = Field(..., min_length=1)
    alias_type: str | None = None
    language: str | None = None
    source_evidence_id: str | None = None


class CompanyIdentifierRequest(BaseModel):
    id_type: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    source_evidence_id: str | None = None


class CompanyEvidenceLinkRequest(BaseModel):
    evidence_id: str
    purpose: str | None = None


@router.post("", response_model=CompanyResponse)
def create_company(
    request: CompanyCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CompanyResponse:
    """Create a company record (idempotent by corporate_number or name)."""
    existing = None
    if request.corporate_number:
        if not (request.corporate_number.isdigit() and len(request.corporate_number) == 13):
            raise HTTPException(status_code=400, detail="corporate_number must be 13 digits")
        existing = (
            db.query(Company)
            .filter(Company.corporate_number == request.corporate_number)
            .first()
        )
    if not existing:
        existing = db.query(Company).filter(Company.name == request.name).first()

    if existing:
        return CompanyResponse(
            company_id=str(existing.id),
            name=existing.name,
            corporate_number=existing.corporate_number,
            normalized_name=existing.normalized_name,
            identity_type=existing.identity_type,
            identity_confidence=existing.identity_confidence,
            existing=True,
        )

    normalized_name = normalize_company_name(request.name)
    country = request.country or ("JP" if request.corporate_number else None)
    company = Company(
        name=request.name,
        corporate_number=request.corporate_number,
        country=country,
        legal_type=request.legal_type,
        normalized_name=normalized_name,
        address_raw=request.address_raw,
        address_pref=request.address_pref,
        address_city=request.address_city,
        status=request.status,
        business_description=request.business_description,
        primary_products=request.primary_products,
        market_regions=request.market_regions,
        is_listed=request.is_listed,
        has_jp_entity=request.has_jp_entity,
        website_url=request.website_url,
        contact_url=request.contact_url,
    )
    db.add(company)
    db.flush()

    if request.aliases:
        for alias in request.aliases:
            alias_value = alias.strip()
            if not alias_value:
                continue
            db.add(
                CompanyAlias(
                    company_id=company.id,
                    alias=alias_value,
                    alias_type="aka",
                )
            )

    db.commit()
    db.refresh(company)

    return CompanyResponse(
        company_id=str(company.id),
        name=company.name,
        corporate_number=company.corporate_number,
        normalized_name=company.normalized_name,
        identity_type=company.identity_type,
        identity_confidence=company.identity_confidence,
        existing=False,
    )


@router.get("/search")
def search_companies(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
    include_aliases: bool = True,
) -> dict:
    """Search companies by name/alias/corporate number."""
    if not q.strip():
        return {"results": []}
    query = db.query(Company)
    normalized = normalize_company_name(q)

    conditions = [
        Company.name.ilike(f"%{q}%"),
        Company.normalized_name.ilike(f"%{normalized}%"),
    ]

    if q.isdigit():
        conditions.append(Company.corporate_number == q)

    if include_aliases:
        query = query.outerjoin(CompanyAlias)
        conditions.append(CompanyAlias.alias.ilike(f"%{q}%"))

    results = (
        query.filter(or_(*conditions))
        .distinct()
        .limit(limit)
        .all()
    )

    return {
        "results": [
            {
                "company_id": str(company.id),
                "name": company.name,
                "corporate_number": company.corporate_number,
                "normalized_name": company.normalized_name,
            }
            for company in results
        ]
    }


@router.get("/{company_id}")
def get_company(
    company_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get a company with aliases and identifiers."""
    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid company ID") from exc

    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return {
        "company_id": str(company.id),
        "name": company.name,
        "corporate_number": company.corporate_number,
        "normalized_name": company.normalized_name,
        "identity_type": company.identity_type,
        "identity_confidence": company.identity_confidence,
        "country": company.country,
        "legal_type": company.legal_type,
        "address_raw": company.address_raw,
        "address_pref": company.address_pref,
        "address_city": company.address_city,
        "status": company.status,
        "business_description": company.business_description,
        "primary_products": company.primary_products,
        "market_regions": company.market_regions,
        "is_listed": company.is_listed,
        "has_jp_entity": company.has_jp_entity,
        "website_url": company.website_url,
        "contact_url": company.contact_url,
        "aliases": [
            {
                "alias": alias.alias,
                "alias_type": alias.alias_type,
                "language": alias.language,
                "source_evidence_id": str(alias.source_evidence_id)
                if alias.source_evidence_id
                else None,
            }
            for alias in company.aliases
        ],
        "identifiers": [
            {
                "id_type": identifier.id_type,
                "value": identifier.value,
                "source_evidence_id": str(identifier.source_evidence_id)
                if identifier.source_evidence_id
                else None,
            }
            for identifier in company.identifiers
        ],
    }


@router.post("/{company_id}/aliases")
def add_company_alias(
    company_id: str,
    request: CompanyAliasRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Add an alias to a company."""
    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid company ID") from exc

    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if request.source_evidence_id:
        try:
            source_evidence_uuid = uuid.UUID(request.source_evidence_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid evidence ID") from exc
    else:
        source_evidence_uuid = None

    existing = (
        db.query(CompanyAlias)
        .filter(CompanyAlias.company_id == company.id, CompanyAlias.alias == request.alias)
        .first()
    )
    if existing:
        return {"alias_id": str(existing.id), "existing": True}

    alias = CompanyAlias(
        company_id=company.id,
        alias=request.alias,
        alias_type=request.alias_type,
        language=request.language,
        source_evidence_id=source_evidence_uuid,
    )
    db.add(alias)
    db.commit()
    db.refresh(alias)

    return {"alias_id": str(alias.id), "existing": False}


@router.post("/{company_id}/identifiers")
def add_company_identifier(
    company_id: str,
    request: CompanyIdentifierRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Add an identifier (EDINET/LEI/etc.) to a company."""
    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid company ID") from exc

    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if request.source_evidence_id:
        try:
            source_evidence_uuid = uuid.UUID(request.source_evidence_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid evidence ID") from exc
    else:
        source_evidence_uuid = None

    existing = (
        db.query(CompanyIdentifier)
        .filter(
            CompanyIdentifier.company_id == company.id,
            CompanyIdentifier.id_type == request.id_type,
            CompanyIdentifier.value == request.value,
        )
        .first()
    )
    if existing:
        return {"identifier_id": str(existing.id), "existing": True}

    identifier = CompanyIdentifier(
        company_id=company.id,
        id_type=request.id_type,
        value=request.value,
        source_evidence_id=source_evidence_uuid,
    )
    db.add(identifier)
    db.commit()
    db.refresh(identifier)

    return {"identifier_id": str(identifier.id), "existing": False}


@router.post("/{company_id}/evidence")
def link_company_evidence(
    company_id: str,
    request: CompanyEvidenceLinkRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Link an evidence record to a company."""
    try:
        company_uuid = uuid.UUID(company_id)
        evidence_uuid = uuid.UUID(request.evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid UUID") from exc

    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    evidence = db.query(Evidence).filter(Evidence.id == evidence_uuid).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    existing = (
        db.query(CompanyEvidenceLink)
        .filter(
            CompanyEvidenceLink.company_id == company.id,
            CompanyEvidenceLink.evidence_id == evidence.id,
            CompanyEvidenceLink.purpose == request.purpose,
        )
        .first()
    )
    if existing:
        return {"link_id": str(existing.id), "existing": True}

    link = CompanyEvidenceLink(
        company_id=company.id,
        evidence_id=evidence.id,
        purpose=request.purpose,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {"link_id": str(link.id), "existing": False}
