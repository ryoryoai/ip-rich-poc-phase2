"""Product master data endpoints."""

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
    Product,
    ProductIdentifier,
    ProductEvidenceLink,
    ProductVersion,
    ProductFact,
    Evidence,
)
from app.services.normalization import normalize_product_name

router = APIRouter()


class ProductCreateRequest(BaseModel):
    company_id: str
    name: str = Field(..., min_length=1)
    model_number: str | None = None
    brand_name: str | None = None
    category_path: str | None = None
    description: str | None = None
    sale_region: str | None = None
    status: str | None = None


class ProductResponse(BaseModel):
    product_id: str
    name: str
    model_number: str | None = None
    normalized_name: str | None = None
    existing: bool = False


class ProductIdentifierRequest(BaseModel):
    id_type: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    source_evidence_id: str | None = None


class ProductEvidenceLinkRequest(BaseModel):
    evidence_id: str
    purpose: str | None = None
    product_version_id: str | None = None


class ProductVersionRequest(BaseModel):
    version_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ProductFactRequest(BaseModel):
    fact_text: str = Field(..., min_length=1)
    product_version_id: str | None = None
    evidence_id: str | None = None


@router.post("", response_model=ProductResponse)
def create_product(
    request: ProductCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    """Create a product record."""
    try:
        company_uuid = uuid.UUID(request.company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid company ID") from exc

    if not db.query(Company).filter(Company.id == company_uuid).first():
        raise HTTPException(status_code=404, detail="Company not found")

    normalized = normalize_product_name(request.name)
    existing = (
        db.query(Product)
        .filter(Product.company_id == company_uuid, Product.name == request.name)
        .first()
    )
    if existing:
        return ProductResponse(
            product_id=str(existing.id),
            name=existing.name,
            model_number=existing.model_number,
            normalized_name=existing.normalized_name,
            existing=True,
        )

    product = Product(
        company_id=company_uuid,
        name=request.name,
        model_number=request.model_number,
        brand_name=request.brand_name,
        category_path=request.category_path,
        description=request.description,
        sale_region=request.sale_region,
        normalized_name=normalized,
        status=request.status,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return ProductResponse(
        product_id=str(product.id),
        name=product.name,
        model_number=product.model_number,
        normalized_name=product.normalized_name,
        existing=False,
    )


@router.post("/{product_id}/versions")
def create_product_version(
    product_id: str,
    request: ProductVersionRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create a product version."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid product ID") from exc

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    version = ProductVersion(
        product_id=product.id,
        version_name=request.version_name,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    return {
        "version_id": str(version.id),
        "product_id": str(product.id),
        "version_name": version.version_name,
        "start_date": version.start_date,
        "end_date": version.end_date,
    }


@router.get("/search")
def search_products(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
    include_identifiers: bool = True,
) -> dict:
    """Search products by name/model/identifier."""
    if not q.strip():
        return {"results": []}
    query = db.query(Product)
    normalized = normalize_product_name(q)

    conditions = [
        Product.name.ilike(f"%{q}%"),
        Product.normalized_name.ilike(f"%{normalized}%"),
    ]

    if include_identifiers:
        query = query.outerjoin(ProductIdentifier)
        conditions.append(ProductIdentifier.value.ilike(f"%{q}%"))

    if q:
        conditions.append(Product.model_number.ilike(f"%{q}%"))

    results = (
        query.filter(or_(*conditions))
        .distinct()
        .limit(limit)
        .all()
    )

    return {
        "results": [
            {
                "product_id": str(product.id),
                "company_id": str(product.company_id),
                "name": product.name,
                "model_number": product.model_number,
                "normalized_name": product.normalized_name,
            }
            for product in results
        ]
    }


@router.get("/{product_id}")
def get_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get a product with identifiers and evidence links."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid product ID") from exc

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "product_id": str(product.id),
        "company_id": str(product.company_id),
        "name": product.name,
        "model_number": product.model_number,
        "brand_name": product.brand_name,
        "category_path": product.category_path,
        "description": product.description,
        "sale_region": product.sale_region,
        "normalized_name": product.normalized_name,
        "status": product.status,
        "identifiers": [
            {
                "id_type": identifier.id_type,
                "value": identifier.value,
                "source_evidence_id": str(identifier.source_evidence_id)
                if identifier.source_evidence_id
                else None,
            }
            for identifier in product.identifiers
        ],
    }


@router.post("/{product_id}/facts")
def create_product_fact(
    product_id: str,
    request: ProductFactRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Add a fact to a product version (creates default version if missing)."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid product ID") from exc

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if request.product_version_id:
        try:
            version_uuid = uuid.UUID(request.product_version_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid product version ID") from exc
        version = db.query(ProductVersion).filter(ProductVersion.id == version_uuid).first()
        if not version:
            raise HTTPException(status_code=404, detail="Product version not found")
        if version.product_id != product.id:
            raise HTTPException(status_code=400, detail="Product version does not belong to product")
    else:
        version = (
            db.query(ProductVersion)
            .filter(ProductVersion.product_id == product.id, ProductVersion.version_name == "default")
            .first()
        )
        if not version:
            version = ProductVersion(product_id=product.id, version_name="default")
            db.add(version)
            db.flush()

    evidence_uuid = None
    if request.evidence_id:
        try:
            evidence_uuid = uuid.UUID(request.evidence_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid evidence ID") from exc
        evidence = db.query(Evidence).filter(Evidence.id == evidence_uuid).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")

    fact = ProductFact(
        product_version_id=version.id,
        fact_text=request.fact_text,
        evidence_id=evidence_uuid,
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)

    return {
        "fact_id": str(fact.id),
        "product_id": str(product.id),
        "product_version_id": str(version.id),
        "fact_text": fact.fact_text,
        "evidence_id": str(fact.evidence_id) if fact.evidence_id else None,
    }


@router.get("/{product_id}/facts")
def list_product_facts(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> dict:
    """List recent facts for a product."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid product ID") from exc

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    facts = (
        db.query(ProductFact)
        .join(ProductVersion, ProductVersion.id == ProductFact.product_version_id)
        .filter(ProductVersion.product_id == product.id)
        .order_by(ProductFact.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "product_id": str(product.id),
        "facts": [
            {
                "fact_id": str(fact.id),
                "product_version_id": str(fact.product_version_id),
                "fact_text": fact.fact_text,
                "evidence_id": str(fact.evidence_id) if fact.evidence_id else None,
            }
            for fact in facts
        ],
    }


@router.post("/{product_id}/identifiers")
def add_product_identifier(
    product_id: str,
    request: ProductIdentifierRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Add an identifier (JAN/GTIN/SKU/Model) to a product."""
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid product ID") from exc

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if request.source_evidence_id:
        try:
            source_evidence_uuid = uuid.UUID(request.source_evidence_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid evidence ID") from exc
    else:
        source_evidence_uuid = None

    existing = (
        db.query(ProductIdentifier)
        .filter(
            ProductIdentifier.product_id == product.id,
            ProductIdentifier.id_type == request.id_type,
            ProductIdentifier.value == request.value,
        )
        .first()
    )
    if existing:
        return {"identifier_id": str(existing.id), "existing": True}

    identifier = ProductIdentifier(
        product_id=product.id,
        id_type=request.id_type,
        value=request.value,
        source_evidence_id=source_evidence_uuid,
    )
    db.add(identifier)
    db.commit()
    db.refresh(identifier)

    return {"identifier_id": str(identifier.id), "existing": False}


@router.post("/{product_id}/evidence")
def link_product_evidence(
    product_id: str,
    request: ProductEvidenceLinkRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Link evidence to a product (optionally to a version)."""
    try:
        product_uuid = uuid.UUID(product_id)
        evidence_uuid = uuid.UUID(request.evidence_id)
        version_uuid = uuid.UUID(request.product_version_id) if request.product_version_id else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid UUID") from exc

    product = db.query(Product).filter(Product.id == product_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    evidence = db.query(Evidence).filter(Evidence.id == evidence_uuid).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if version_uuid:
        version = db.query(ProductVersion).filter(ProductVersion.id == version_uuid).first()
        if not version:
            raise HTTPException(status_code=404, detail="Product version not found")
    else:
        version = None

    existing = (
        db.query(ProductEvidenceLink)
        .filter(
            ProductEvidenceLink.product_id == product.id,
            ProductEvidenceLink.product_version_id == (version.id if version else None),
            ProductEvidenceLink.evidence_id == evidence.id,
        )
        .first()
    )
    if existing:
        return {"link_id": str(existing.id), "existing": True}

    link = ProductEvidenceLink(
        product_id=product.id,
        product_version_id=version.id if version else None,
        evidence_id=evidence.id,
        purpose=request.purpose,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {"link_id": str(link.id), "existing": False}
