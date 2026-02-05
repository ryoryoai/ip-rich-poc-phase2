"""SQLAlchemy models for Phase2 patent storage and analysis.

Merged from Phase1 (Prisma) and Phase2 (SQLAlchemy) schemas.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# =============================================================================
# RAW FILE STORAGE (Phase2 original)
# =============================================================================

class RawFile(Base):
    """Raw file (ZIP/XML) metadata."""

    __tablename__ = "raw_files"
    __table_args__ = {"schema": "phase2"}

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: str = Column(String(50), nullable=False)
    original_name: str = Column(String(255), nullable=False)
    sha256: str = Column(String(64), unique=True, nullable=False)
    stored_path: str = Column(Text, nullable=False)
    storage_provider: Optional[str] = Column(String(20))
    bucket: Optional[str] = Column(String(100))
    object_path: Optional[str] = Column(Text)
    mime_type: Optional[str] = Column(String(100))
    size_bytes: Optional[int] = Column(BigInteger)
    etag: Optional[str] = Column(String(100))
    acquired_at: Optional[datetime] = Column(DateTime(timezone=True))
    metadata_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    documents = relationship("Document", back_populates="raw_file")
    versions = relationship("PatentVersion", back_populates="raw_file")


class IngestRun(Base):
    """Ingest run history."""

    __tablename__ = "ingest_runs"
    __table_args__ = {"schema": "phase2"}

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_type: str = Column(String(20), nullable=False)
    started_at: Optional[datetime] = Column(DateTime(timezone=True))
    finished_at: Optional[datetime] = Column(DateTime(timezone=True))
    status: str = Column(String(20), nullable=False, default="running")
    detail_json: Optional[dict] = Column(JSON)


# =============================================================================
# PATENT DATA (Merged: Phase1 patent_cases + Phase2 documents)
# =============================================================================

class Document(Base):
    """Patent document information (patent_cases equivalent)."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("country", "doc_number", "kind", name="uq_documents_country_number_kind"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country: str = Column(String(2), nullable=False)
    doc_number: str = Column(String(20), nullable=False)
    kind: Optional[str] = Column(String(10))
    publication_date: Optional[datetime] = Column(Date)

    # Additional fields from Phase1 patent_cases
    title: Optional[str] = Column(Text)
    abstract: Optional[str] = Column(Text)
    assignee: Optional[str] = Column(Text)
    filing_date: Optional[str] = Column(String(20))

    raw_file_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.raw_files.id")
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    raw_file = relationship("RawFile", back_populates="documents")
    claims = relationship("Claim", back_populates="document", cascade="all, delete-orphan")
    sources = relationship("PatentSource", back_populates="document", cascade="all, delete-orphan")
    texts = relationship("DocumentText", back_populates="document", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="document")
    company_links = relationship("PatentCompanyLink", back_populates="document", cascade="all, delete-orphan")


class DocumentText(Base):
    """Long-form document text (specification, full description, etc.)."""

    __tablename__ = "document_texts"
    __table_args__ = (
        Index("idx_document_texts_document", "document_id"),
        Index("idx_document_texts_type", "text_type"),
        Index("idx_document_texts_current", "document_id", "text_type", "is_current"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.documents.id"), nullable=False
    )
    text_type: str = Column(String(30), nullable=False)  # specification/description/claims_full
    language: Optional[str] = Column(String(8))
    source: Optional[str] = Column(String(30))  # gazette/jplatpat/llm
    is_current: bool = Column(Boolean, default=True)
    text: str = Column(Text, nullable=False)
    metadata_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    document = relationship("Document", back_populates="texts")


class PatentSource(Base):
    """Source data for patent information (J-PlatPat, Google Patents, etc.)."""

    __tablename__ = "patent_sources"
    __table_args__ = (
        Index("idx_patent_sources_document", "document_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.documents.id"), nullable=False
    )
    source: str = Column(Text, nullable=False)  # 'jplatpat', 'google_patents', etc.
    payload: Optional[dict] = Column(JSON)
    retrieved_at: Optional[datetime] = Column(DateTime(timezone=True))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    document = relationship("Document", back_populates="sources")


class Claim(Base):
    """Patent claim."""

    __tablename__ = "claims"
    __table_args__ = (
        UniqueConstraint("document_id", "claim_no", name="uq_claims_document_claim_no"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.documents.id"), nullable=False
    )
    claim_no: int = Column(Integer, nullable=False)
    claim_text: str = Column(Text, nullable=False)
    source: Optional[str] = Column(String(30))
    is_current: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    document = relationship("Document", back_populates="claims")
    elements = relationship("ClaimElement", back_populates="claim", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="claim")


class ClaimElement(Base):
    """Individual element within a patent claim."""

    __tablename__ = "claim_elements"
    __table_args__ = (
        UniqueConstraint("claim_id", "element_no", name="uq_claim_elements_claim_element_no"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.claims.id"), nullable=False
    )
    element_no: int = Column(Integer, nullable=False)
    quote_text: str = Column(Text, nullable=False)  # Original text from claim
    normalized_text: Optional[str] = Column(Text)  # LLM-normalized version
    metadata_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="elements")
    assessments = relationship("ElementAssessment", back_populates="claim_element")


# =============================================================================
# PATENT TEXT STORAGE (New)
# =============================================================================

class Patent(Base):
    """Internal patent identity and normalized numbers."""

    __tablename__ = "patents"
    __table_args__ = {"schema": "phase2"}

    internal_patent_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction: str = Column(String(2), nullable=False, default="JP")
    application_no: Optional[str] = Column(String(40))
    publication_no: Optional[str] = Column(String(40))
    registration_no: Optional[str] = Column(String(40))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    number_sources = relationship(
        "PatentNumberSource", back_populates="patent", cascade="all, delete-orphan"
    )
    versions = relationship(
        "PatentVersion", back_populates="patent", cascade="all, delete-orphan"
    )


class PatentNumberSource(Base):
    """Source records for patent number normalization."""

    __tablename__ = "patent_number_sources"
    __table_args__ = (
        UniqueConstraint(
            "internal_patent_id",
            "number_type",
            "number_value_raw",
            "source_type",
            name="uq_patent_number_sources",
        ),
        Index("idx_patent_number_sources_patent", "internal_patent_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    internal_patent_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.patents.internal_patent_id"), nullable=False
    )
    number_type: str = Column(String(20), nullable=False)
    number_value_raw: str = Column(Text, nullable=False)
    number_value_norm: Optional[str] = Column(Text)
    source_type: str = Column(String(20), nullable=False)
    source_ref: Optional[str] = Column(Text)
    retrieved_at: Optional[datetime] = Column(DateTime(timezone=True))
    confidence: Optional[float] = Column(Float)

    # Relationships
    patent = relationship("Patent", back_populates="number_sources")


class PatentVersion(Base):
    """Patent text version (gazette, correction, republication)."""

    __tablename__ = "patent_versions"
    __table_args__ = (
        Index("idx_patent_versions_internal", "internal_patent_id"),
        {"schema": "phase2"},
    )

    version_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    internal_patent_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.patents.internal_patent_id"), nullable=False
    )
    publication_type: str = Column(String(20), nullable=False)
    kind_code: Optional[str] = Column(String(10))
    gazette_number: Optional[str] = Column(String(40))
    issue_date: Optional[datetime] = Column(Date)
    language: str = Column(String(8), default="ja")
    source_type: str = Column(String(20), nullable=False)
    source_ref: Optional[str] = Column(Text)
    raw_file_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.raw_files.id")
    )
    raw_object_uri: Optional[str] = Column(Text)
    content_hash: Optional[str] = Column(String(64))
    parse_status: Optional[str] = Column(String(20))
    parse_result_json: Optional[dict] = Column(JSON)
    norm_version: Optional[str] = Column(String(20))
    is_latest: bool = Column(Boolean, nullable=False, default=False)
    acquired_at: Optional[datetime] = Column(DateTime(timezone=True))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    patent = relationship("Patent", back_populates="versions")
    raw_file = relationship("RawFile", back_populates="versions")
    claims = relationship("PatentClaim", back_populates="version", cascade="all, delete-orphan")
    spec_sections = relationship(
        "PatentSpecSection", back_populates="version", cascade="all, delete-orphan"
    )


class PatentClaim(Base):
    """Patent claim text (per version)."""

    __tablename__ = "patent_claims"
    __table_args__ = (
        UniqueConstraint("version_id", "claim_no", name="uq_patent_claims_version_claim_no"),
        Index("idx_patent_claims_version", "version_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.patent_versions.version_id"), nullable=False
    )
    claim_no: int = Column(Integer, nullable=False)
    text_raw: str = Column(Text, nullable=False)
    text_norm: Optional[str] = Column(Text)
    norm_version: Optional[str] = Column(String(20))

    # Relationships
    version = relationship("PatentVersion", back_populates="claims")


class PatentSpecSection(Base):
    """Patent specification sections (per version)."""

    __tablename__ = "patent_spec_sections"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "section_type",
            "order_no",
            name="uq_patent_spec_sections_version_section_order",
        ),
        Index("idx_patent_spec_sections_version", "version_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.patent_versions.version_id"), nullable=False
    )
    section_type: str = Column(String(40), nullable=False)
    order_no: int = Column(Integer, nullable=False)
    text_raw: str = Column(Text, nullable=False)
    text_norm: Optional[str] = Column(Text)
    norm_version: Optional[str] = Column(String(20))

    # Relationships
    version = relationship("PatentVersion", back_populates="spec_sections")


class IngestionJob(Base):
    """Ingestion job for patent text acquisition."""

    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("idx_ingestion_jobs_status", "status"),
        Index("idx_ingestion_jobs_created_at", "created_at"),
        {"schema": "phase2"},
    )

    job_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: str = Column(String(20), nullable=False, default="queued")
    priority: int = Column(Integer, default=5, nullable=False)
    force_refresh: bool = Column(Boolean, nullable=False, default=False)
    source_preference: Optional[str] = Column(String(20))
    idempotency_key: Optional[str] = Column(String(80), unique=True)
    retry_count: int = Column(Integer, default=0, nullable=False)
    max_retries: int = Column(Integer, default=3, nullable=False)
    error_code: Optional[str] = Column(String(50))
    error_detail: Optional[str] = Column(Text)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    started_at: Optional[datetime] = Column(DateTime(timezone=True))
    finished_at: Optional[datetime] = Column(DateTime(timezone=True))

    # Relationships
    items = relationship("IngestionJobItem", back_populates="job", cascade="all, delete-orphan")


class IngestionJobItem(Base):
    """Individual patent ingestion item within a job."""

    __tablename__ = "ingestion_job_items"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "input_number",
            "input_number_type",
            name="uq_ingestion_job_items",
        ),
        Index("idx_ingestion_job_items_job", "job_id"),
        {"schema": "phase2"},
    )

    job_item_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.ingestion_jobs.job_id"), nullable=False
    )
    internal_patent_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.patents.internal_patent_id")
    )
    input_number: str = Column(Text, nullable=False)
    input_number_type: str = Column(String(20), nullable=False)
    status: str = Column(String(20), nullable=False)
    retry_count: int = Column(Integer, default=0, nullable=False)
    error_code: Optional[str] = Column(String(50))
    error_detail: Optional[str] = Column(Text)
    target_version_hint: Optional[dict] = Column(JSON)

    # Relationships
    job = relationship("IngestionJob", back_populates="items")
    patent = relationship("Patent")


# =============================================================================
# AUTO COLLECTION (Company/Product ingestion and crawl jobs)
# =============================================================================

class CollectionJob(Base):
    """Generic collection job for company/product ingestion."""

    __tablename__ = "collection_jobs"
    __table_args__ = (
        Index("idx_collection_jobs_status", "status"),
        Index("idx_collection_jobs_created_at", "created_at"),
        {"schema": "phase2"},
    )

    job_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type: str = Column(String(30), nullable=False)
    status: str = Column(String(20), nullable=False, default="queued")
    priority: int = Column(Integer, default=5, nullable=False)
    retry_count: int = Column(Integer, default=0, nullable=False)
    max_retries: int = Column(Integer, default=3, nullable=False)
    error_code: Optional[str] = Column(String(50))
    error_detail: Optional[str] = Column(Text)
    metrics_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    started_at: Optional[datetime] = Column(DateTime(timezone=True))
    finished_at: Optional[datetime] = Column(DateTime(timezone=True))

    items = relationship("CollectionItem", back_populates="job", cascade="all, delete-orphan")


class CollectionItem(Base):
    """Collection item within a collection job."""

    __tablename__ = "collection_items"
    __table_args__ = (
        Index("idx_collection_items_job", "job_id"),
        Index("idx_collection_items_status", "status"),
        {"schema": "phase2"},
    )

    item_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.collection_jobs.job_id"), nullable=False
    )
    entity_type: str = Column(String(20), nullable=False)
    entity_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True))
    source_type: Optional[str] = Column(String(30))
    source_ref: Optional[str] = Column(Text)
    status: str = Column(String(20), nullable=False, default="queued")
    retry_count: int = Column(Integer, default=0, nullable=False)
    error_code: Optional[str] = Column(String(50))
    error_detail: Optional[str] = Column(Text)
    payload_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    started_at: Optional[datetime] = Column(DateTime(timezone=True))
    finished_at: Optional[datetime] = Column(DateTime(timezone=True))

    job = relationship("CollectionJob", back_populates="items")


# =============================================================================
# COMPANY & PRODUCT DATA (From Phase1)
# =============================================================================

class Company(Base):
    """Company information."""

    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("name", name="uq_companies_name"),
        UniqueConstraint("corporate_number", name="uq_companies_corporate_number"),
        Index("idx_companies_corporate_number", "corporate_number"),
        Index("idx_companies_normalized_name", "normalized_name"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: str = Column(Text, nullable=False)
    corporate_number: Optional[str] = Column(String(13))
    country: Optional[str] = Column(String(2))
    legal_type: Optional[str] = Column(String(50))
    normalized_name: Optional[str] = Column(Text)
    address_raw: Optional[str] = Column(Text)
    address_pref: Optional[str] = Column(String(20))
    address_city: Optional[str] = Column(String(50))
    status: Optional[str] = Column(String(20))
    business_description: Optional[str] = Column(Text)
    primary_products: Optional[str] = Column(Text)
    market_regions: Optional[str] = Column(Text)
    is_listed: Optional[bool] = Column(Boolean, default=False)
    has_jp_entity: Optional[bool] = Column(Boolean, default=True)
    website_url: Optional[str] = Column(Text)
    contact_url: Optional[str] = Column(Text)
    identity_type: str = Column(String(20), nullable=False, default="provisional")
    identity_confidence: float = Column(Float, default=50)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    aliases = relationship("CompanyAlias", back_populates="company", cascade="all, delete-orphan")
    identifiers = relationship("CompanyIdentifier", back_populates="company", cascade="all, delete-orphan")
    evidence_links = relationship("CompanyEvidenceLink", back_populates="company", cascade="all, delete-orphan")
    field_values = relationship("CompanyFieldValue", back_populates="company", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    product_links = relationship("CompanyProductLink", back_populates="company", cascade="all, delete-orphan")
    patent_links = relationship("PatentCompanyLink", back_populates="company", cascade="all, delete-orphan")


class CompanyAlias(Base):
    """Alternative names for companies."""

    __tablename__ = "company_aliases"
    __table_args__ = (
        UniqueConstraint("company_id", "alias", name="uq_company_aliases_company_alias"),
        Index("idx_company_aliases_alias", "alias"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    alias: str = Column(Text, nullable=False)
    alias_type: Optional[str] = Column(String(30))
    language: Optional[str] = Column(String(8))
    source_evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    company = relationship("Company", back_populates="aliases")
    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])


class CompanyIdentifier(Base):
    """External identifiers for companies (EDINET, LEI, D-U-N-S, etc.)."""

    __tablename__ = "company_identifiers"
    __table_args__ = (
        UniqueConstraint("company_id", "id_type", "value", name="uq_company_identifiers"),
        Index("idx_company_identifiers_value", "value"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    id_type: str = Column(String(30), nullable=False)
    value: str = Column(String(100), nullable=False)
    source_evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    company = relationship("Company", back_populates="identifiers")
    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])


class CompanyFieldValue(Base):
    """Field-level evidence/history for company attributes."""

    __tablename__ = "company_field_values"
    __table_args__ = (
        Index("idx_company_field_values_company", "company_id"),
        Index("idx_company_field_values_current", "company_id", "field_name", "is_current"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    field_name: str = Column(String(64), nullable=False)
    value_text: Optional[str] = Column(Text)
    value_json: Optional[dict] = Column(JSON)
    value_hash: Optional[str] = Column(String(64))
    source_evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    source_type: Optional[str] = Column(String(30))
    source_ref: Optional[str] = Column(Text)
    confidence_score: Optional[float] = Column(Float)
    captured_at: Optional[datetime] = Column(DateTime(timezone=True))
    is_current: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    company = relationship("Company", back_populates="field_values")
    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])


class Product(Base):
    """Product information."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_products_company_name"),
        Index("idx_products_model_number", "model_number"),
        Index("idx_products_normalized_name", "normalized_name"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    name: str = Column(Text, nullable=False)
    model_number: Optional[str] = Column(Text)
    brand_name: Optional[str] = Column(Text)
    category_path: Optional[str] = Column(Text)
    description: Optional[str] = Column(Text)
    sale_region: Optional[str] = Column(Text)
    normalized_name: Optional[str] = Column(Text)
    status: Optional[str] = Column(String(20))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    company = relationship("Company", back_populates="products")
    identifiers = relationship("ProductIdentifier", back_populates="product", cascade="all, delete-orphan")
    evidence_links = relationship("ProductEvidenceLink", back_populates="product", cascade="all, delete-orphan")
    company_links = relationship("CompanyProductLink", back_populates="product", cascade="all, delete-orphan")
    field_values = relationship("ProductFieldValue", back_populates="product", cascade="all, delete-orphan")
    versions = relationship("ProductVersion", back_populates="product", cascade="all, delete-orphan")


class ProductIdentifier(Base):
    """External identifiers for products (JAN/GTIN/SKU/Model)."""

    __tablename__ = "product_identifiers"
    __table_args__ = (
        UniqueConstraint("product_id", "id_type", "value", name="uq_product_identifiers"),
        Index("idx_product_identifiers_value", "value"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.products.id"), nullable=False
    )
    id_type: str = Column(String(30), nullable=False)
    value: str = Column(String(100), nullable=False)
    source_evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    product = relationship("Product", back_populates="identifiers")
    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])


class ProductFieldValue(Base):
    """Field-level evidence/history for product attributes."""

    __tablename__ = "product_field_values"
    __table_args__ = (
        Index("idx_product_field_values_product", "product_id"),
        Index("idx_product_field_values_current", "product_id", "field_name", "is_current"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.products.id"), nullable=False
    )
    field_name: str = Column(String(64), nullable=False)
    value_text: Optional[str] = Column(Text)
    value_json: Optional[dict] = Column(JSON)
    value_hash: Optional[str] = Column(String(64))
    source_evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    source_type: Optional[str] = Column(String(30))
    source_ref: Optional[str] = Column(Text)
    confidence_score: Optional[float] = Column(Float)
    captured_at: Optional[datetime] = Column(DateTime(timezone=True))
    is_current: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    product = relationship("Product", back_populates="field_values")
    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])


class ProductVersion(Base):
    """Product version with date range."""

    __tablename__ = "product_versions"
    __table_args__ = (
        Index("idx_product_versions_product", "product_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.products.id"), nullable=False
    )
    version_name: Optional[str] = Column(Text)
    start_date: Optional[str] = Column(String(20))
    end_date: Optional[str] = Column(String(20))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    product = relationship("Product", back_populates="versions")
    facts = relationship("ProductFact", back_populates="product_version", cascade="all, delete-orphan")
    assessments = relationship("ElementAssessment", back_populates="product_version")


class TechKeyword(Base):
    """Technical keyword dictionary for overseas exploration."""

    __tablename__ = "tech_keywords"
    __table_args__ = (
        Index("idx_tech_keywords_term", "term"),
        Index("idx_tech_keywords_language", "language"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term: str = Column(Text, nullable=False)
    language: str = Column(String(8), nullable=False, default="ja")
    normalized_term: Optional[str] = Column(Text)
    synonyms: Optional[list] = Column(JSON)
    abbreviations: Optional[list] = Column(JSON)
    domain: Optional[str] = Column(Text)
    notes: Optional[str] = Column(Text)
    source_evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    source_evidence = relationship("Evidence", foreign_keys=[source_evidence_id])


# =============================================================================
# EVIDENCE DATA (From Phase1)
# =============================================================================

class Evidence(Base):
    """Evidence from web search or documents."""

    __tablename__ = "evidence"
    __table_args__ = (
        Index("idx_evidence_url", "url"),
        Index("idx_evidence_content_hash", "content_hash"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: str = Column(Text, nullable=False)
    source_type: Optional[str] = Column(String(50))
    title: Optional[str] = Column(Text)
    quote_text: Optional[str] = Column(Text)
    retrieved_at: Optional[datetime] = Column(DateTime(timezone=True))
    captured_at: Optional[datetime] = Column(DateTime(timezone=True))
    content_hash: Optional[str] = Column(String(64))
    content_type: Optional[str] = Column(String(100))
    storage_path: Optional[str] = Column(Text)
    raw: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    company_links = relationship("CompanyEvidenceLink", back_populates="evidence")
    product_links = relationship("ProductEvidenceLink", back_populates="evidence")
    product_facts = relationship("ProductFact", back_populates="evidence")
    assessment_links = relationship("ElementAssessmentEvidence", back_populates="evidence")


class CompanyEvidenceLink(Base):
    """Link between company and evidence."""

    __tablename__ = "company_evidence_links"
    __table_args__ = (
        UniqueConstraint("company_id", "evidence_id", "purpose", name="uq_company_evidence_links"),
        Index("idx_company_evidence_links_company", "company_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    evidence_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id"), nullable=False
    )
    purpose: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    company = relationship("Company", back_populates="evidence_links")
    evidence = relationship("Evidence", back_populates="company_links")


class ProductEvidenceLink(Base):
    """Link between product (and optional version) and evidence."""

    __tablename__ = "product_evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "product_version_id", "evidence_id",
            name="uq_product_evidence_links"
        ),
        Index("idx_product_evidence_links_product", "product_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.products.id"), nullable=False
    )
    product_version_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.product_versions.id")
    )
    evidence_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id"), nullable=False
    )
    purpose: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    product = relationship("Product", back_populates="evidence_links")
    product_version = relationship("ProductVersion")
    evidence = relationship("Evidence", back_populates="product_links")


class ProductFact(Base):
    """Facts about a product version, linked to evidence."""

    __tablename__ = "product_facts"
    __table_args__ = (
        Index("idx_product_facts_version", "product_version_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_version_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.product_versions.id"), nullable=False
    )
    fact_text: str = Column(Text, nullable=False)
    evidence_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id")
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    product_version = relationship("ProductVersion", back_populates="facts")
    evidence = relationship("Evidence", back_populates="product_facts")


class CompanyProductLink(Base):
    """Link between company and product with role and confidence."""

    __tablename__ = "company_product_links"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "product_id", "role",
            name="uq_company_product_links_company_product_role"
        ),
        Index("idx_company_product_links_company", "company_id"),
        Index("idx_company_product_links_product", "product_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    product_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.products.id"), nullable=False
    )
    role: str = Column(String(30), nullable=False)  # manufacturer/owner/seller/distributor
    link_type: str = Column(String(20), nullable=False)  # deterministic/probabilistic
    confidence_score: Optional[float] = Column(Float)
    review_status: str = Column(String(20), nullable=False, default="pending")
    review_note: Optional[str] = Column(Text)
    evidence_json: Optional[dict] = Column(JSON)
    verified_by: Optional[str] = Column(Text)
    verified_at: Optional[datetime] = Column(DateTime(timezone=True))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    company = relationship("Company", back_populates="product_links")
    product = relationship("Product", back_populates="company_links")


class PatentCompanyLink(Base):
    """Link between patent (document) and company."""

    __tablename__ = "patent_company_links"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "patent_ref", "company_id", "role",
            name="uq_patent_company_links_doc_patent_company_role"
        ),
        Index("idx_patent_company_links_company", "company_id"),
        Index("idx_patent_company_links_document", "document_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.documents.id")
    )
    patent_ref: Optional[str] = Column(String(40))  # publication/application/patent number
    company_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id"), nullable=False
    )
    role: str = Column(String(30), nullable=False)  # applicant/assignee/licensee
    link_type: str = Column(String(20), nullable=False)  # deterministic/probabilistic
    confidence_score: Optional[float] = Column(Float)
    review_status: str = Column(String(20), nullable=False, default="pending")
    review_note: Optional[str] = Column(Text)
    evidence_json: Optional[dict] = Column(JSON)
    verified_by: Optional[str] = Column(Text)
    verified_at: Optional[datetime] = Column(DateTime(timezone=True))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    document = relationship("Document", back_populates="company_links")
    company = relationship("Company", back_populates="patent_links")


# =============================================================================
# JP PATENT INDEX (JP Patent Index v0.1)
# =============================================================================

class JpAuditLog(Base):
    """Audit log for JP Index access."""

    __tablename__ = "jp_audit_logs"
    __table_args__ = (
        Index("idx_jp_audit_logs_created_at", "created_at"),
        Index("idx_jp_audit_logs_action", "action"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action: str = Column(String(50), nullable=False)
    resource_id: Optional[str] = Column(String(64))
    request_path: Optional[str] = Column(Text)
    method: Optional[str] = Column(String(10))
    client_ip: Optional[str] = Column(String(64))
    user_agent: Optional[str] = Column(Text)
    payload_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

class JpIngestBatch(Base):
    """Ingest batch for JP Patent Index."""

    __tablename__ = "jp_ingest_batches"
    __table_args__ = (
        UniqueConstraint("batch_key", name="uq_jp_ingest_batches_batch_key"),
        Index("idx_jp_ingest_batches_update_date", "update_date"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: str = Column(String(50), nullable=False)
    run_type: str = Column(String(20), nullable=False)  # full/delta/weekly/authority
    update_date: Optional[datetime] = Column(Date)
    batch_key: str = Column(String(100), nullable=False)
    status: str = Column(String(20), nullable=False, default="running")
    started_at: Optional[datetime] = Column(DateTime(timezone=True))
    finished_at: Optional[datetime] = Column(DateTime(timezone=True))
    counts_json: Optional[dict] = Column(JSON)
    metadata_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    files = relationship("JpIngestBatchFile", back_populates="batch", cascade="all, delete-orphan")


class JpIngestBatchFile(Base):
    """Link between ingest batch and raw files."""

    __tablename__ = "jp_ingest_batch_files"
    __table_args__ = (
        UniqueConstraint("batch_id", "raw_file_id", name="uq_jp_ingest_batch_files_batch_raw"),
        Index("idx_jp_ingest_batch_files_raw_file", "raw_file_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_ingest_batches.id"), nullable=False)
    raw_file_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("phase2.raw_files.id"))
    file_sha256: Optional[str] = Column(String(64))
    original_name: Optional[str] = Column(String(255))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    batch = relationship("JpIngestBatch", back_populates="files")
    raw_file = relationship("RawFile")


class JpCase(Base):
    """JP patent case (application-level)."""

    __tablename__ = "jp_cases"
    __table_args__ = (
        Index("idx_jp_cases_application_number_norm", "application_number_norm"),
        Index("idx_jp_cases_status", "current_status"),
        Index("idx_jp_cases_last_update_date", "last_update_date"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country: str = Column(String(2), nullable=False, default="JP")
    application_number_raw: Optional[str] = Column(String(40))
    application_number_norm: Optional[str] = Column(String(40))
    filing_date: Optional[datetime] = Column(Date)
    title: Optional[str] = Column(Text)
    abstract: Optional[str] = Column(Text)
    current_status: Optional[str] = Column(String(20))
    status_updated_at: Optional[datetime] = Column(DateTime(timezone=True))
    last_update_date: Optional[datetime] = Column(Date)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    documents = relationship("JpDocument", back_populates="case", cascade="all, delete-orphan")
    number_aliases = relationship("JpNumberAlias", back_populates="case", cascade="all, delete-orphan")
    applicants = relationship("JpCaseApplicant", back_populates="case", cascade="all, delete-orphan")
    classifications = relationship("JpClassification", back_populates="case", cascade="all, delete-orphan")
    status_events = relationship("JpStatusEvent", back_populates="case", cascade="all, delete-orphan")
    status_snapshots = relationship("JpStatusSnapshot", back_populates="case", cascade="all, delete-orphan")
    search_document = relationship("JpSearchDocument", back_populates="case", uselist=False)


class JpDocument(Base):
    """Publication/registration document."""

    __tablename__ = "jp_documents"
    __table_args__ = (
        Index("idx_jp_documents_publication_number_norm", "publication_number_norm"),
        Index("idx_jp_documents_patent_number_norm", "patent_number_norm"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    doc_type: str = Column(String(20), nullable=False)  # publication/registration
    publication_number_raw: Optional[str] = Column(String(40))
    publication_number_norm: Optional[str] = Column(String(40))
    patent_number_raw: Optional[str] = Column(String(40))
    patent_number_norm: Optional[str] = Column(String(40))
    kind: Optional[str] = Column(String(10))
    publication_date: Optional[datetime] = Column(Date)
    raw_file_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("phase2.raw_files.id"))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    case = relationship("JpCase", back_populates="documents")
    raw_file = relationship("RawFile")


class JpNumberAlias(Base):
    """Number normalization and cross-reference."""

    __tablename__ = "jp_number_aliases"
    __table_args__ = (
        UniqueConstraint("number_type", "number_norm", name="uq_jp_number_aliases_type_norm"),
        Index("idx_jp_number_aliases_number_norm", "number_norm"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    document_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_documents.id"))
    number_type: str = Column(String(20), nullable=False)  # application/publication/patent
    number_raw: Optional[str] = Column(String(40))
    number_norm: str = Column(String(40), nullable=False)
    country: str = Column(String(2), nullable=False, default="JP")
    kind: Optional[str] = Column(String(10))
    is_primary: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    case = relationship("JpCase", back_populates="number_aliases")
    document = relationship("JpDocument")


class JpApplicant(Base):
    """Applicant master."""

    __tablename__ = "jp_applicants"
    __table_args__ = (
        Index("idx_jp_applicants_name_norm", "name_norm"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_raw: str = Column(Text, nullable=False)
    name_norm: Optional[str] = Column(Text)
    normalize_confidence: Optional[float] = Column(Float)
    source: Optional[str] = Column(String(20))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    cases = relationship("JpCaseApplicant", back_populates="applicant", cascade="all, delete-orphan")


class JpCaseApplicant(Base):
    """Link between JP case and applicant."""

    __tablename__ = "jp_case_applicants"
    __table_args__ = (
        UniqueConstraint("case_id", "applicant_id", "role", name="uq_jp_case_applicants_case_app_role"),
        Index("idx_jp_case_applicants_case", "case_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    applicant_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_applicants.id"), nullable=False)
    role: str = Column(String(20), nullable=False, default="applicant")
    is_primary: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    case = relationship("JpCase", back_populates="applicants")
    applicant = relationship("JpApplicant", back_populates="cases")


class JpClassification(Base):
    """Classification codes for JP case."""

    __tablename__ = "jp_classifications"
    __table_args__ = (
        UniqueConstraint("case_id", "type", "code", name="uq_jp_classifications_case_type_code"),
        Index("idx_jp_classifications_type_code", "type", "code"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    type: str = Column(String(10), nullable=False)  # IPC/FI/FTERM
    code: str = Column(String(64), nullable=False)
    version: Optional[str] = Column(String(20))
    is_primary: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    case = relationship("JpCase", back_populates="classifications")


class JpStatusEvent(Base):
    """Status events with source payload."""

    __tablename__ = "jp_status_events"
    __table_args__ = (
        UniqueConstraint("case_id", "event_type", "event_date", "source", name="uq_jp_status_events_case"),
        Index("idx_jp_status_events_case_date", "case_id", "event_date"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    event_date: Optional[datetime] = Column(Date)
    event_type: str = Column(String(40), nullable=False)
    source: Optional[str] = Column(String(40))
    payload_json: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    case = relationship("JpCase", back_populates="status_events")


class JpStatusSnapshot(Base):
    """Derived status snapshot for JP case."""

    __tablename__ = "jp_status_snapshots"
    __table_args__ = (
        Index("idx_jp_status_snapshots_case", "case_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    status: str = Column(String(20), nullable=False)
    derived_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    logic_version: str = Column(String(20), nullable=False, default="v1")
    basis_event_ids: Optional[dict] = Column(JSON)
    reason: Optional[str] = Column(Text)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    case = relationship("JpCase", back_populates="status_snapshots")


class JpSearchDocument(Base):
    """Search index for JP cases (Postgres FTS)."""

    __tablename__ = "jp_search_documents"
    __table_args__ = (
        UniqueConstraint("case_id", name="uq_jp_search_documents_case"),
        Index("idx_jp_search_documents_status", "status"),
        Index("idx_jp_search_documents_tsv", "tsv", postgresql_using="gin"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_cases.id"), nullable=False)
    document_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("phase2.jp_documents.id"))
    title: Optional[str] = Column(Text)
    abstract: Optional[str] = Column(Text)
    applicants_text: Optional[str] = Column(Text)
    classifications_text: Optional[str] = Column(Text)
    status: Optional[str] = Column(String(20))
    publication_date: Optional[datetime] = Column(Date)
    tsv: Optional[str] = Column(TSVECTOR().with_variant(Text, "sqlite"))
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    case = relationship("JpCase", back_populates="search_document")
    document = relationship("JpDocument")


# =============================================================================
# ANALYSIS JOB (Merged: Phase1 analysis_jobs + Phase2 AnalysisJob)
# =============================================================================

class AnalysisJob(Base):
    """Analysis job for patent infringement investigation."""

    __tablename__ = "analysis_jobs"
    __table_args__ = (
        Index("idx_analysis_jobs_status", "status"),
        Index("idx_analysis_jobs_created_at", "created_at"),
        Index("idx_analysis_jobs_user_id", "user_id"),
        Index("idx_analysis_jobs_company_id", "company_id"),
        Index("idx_analysis_jobs_product_id", "product_id"),
        Index("idx_analysis_jobs_queue", "status", "priority", "scheduled_for"),
        Index("idx_analysis_jobs_batch", "batch_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Status tracking
    status: str = Column(String(20), nullable=False, default="pending")
    # pending, researching, analyzing, completed, failed
    progress: int = Column(Integer, default=0)
    error_message: Optional[str] = Column(Text)

    # Input data
    patent_id: str = Column(String(30), nullable=False)  # patent_number in Phase1
    claim_text: Optional[str] = Column(Text)
    company_name: Optional[str] = Column(Text)
    product_name: Optional[str] = Column(Text)  # target_product in Phase2
    company_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.companies.id")
    )
    product_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.products.id")
    )

    # Pipeline configuration (Phase2)
    pipeline: str = Column(String(20), default="C")  # 'A', 'B', 'C', 'full'
    current_stage: Optional[str] = Column(String(50))

    # Deep Research integration (Phase1)
    openai_response_id: Optional[str] = Column(Text)
    input_prompt: Optional[str] = Column(Text)
    research_results: Optional[dict] = Column(JSON)

    # Analysis results (Phase1)
    requirements: Optional[dict] = Column(JSON)
    compliance_results: Optional[dict] = Column(JSON)
    summary: Optional[dict] = Column(JSON)

    # Batch processing (Phase1)
    priority: int = Column(Integer, default=5)  # 0-10
    scheduled_for: Optional[datetime] = Column(DateTime(timezone=True))
    retry_count: int = Column(Integer, default=0)
    max_retries: int = Column(Integer, default=3)
    batch_id: Optional[str] = Column(Text)
    search_type: str = Column(Text, default="infringement_check")

    # Additional analysis results
    infringement_score: Optional[float] = Column(Float)  # 0-100
    revenue_estimate: Optional[dict] = Column(JSON)

    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)
    queued_at: Optional[datetime] = Column(DateTime(timezone=True))
    started_at: Optional[datetime] = Column(DateTime(timezone=True))
    completed_at: Optional[datetime] = Column(DateTime(timezone=True))  # finished_at in Phase1

    # Context & Metadata
    context_json: Optional[dict] = Column(JSON)  # Accumulated context between stages
    user_id: Optional[uuid.UUID] = Column(UUID(as_uuid=True))
    ip_address: Optional[str] = Column(Text)

    # Relationships
    results = relationship("AnalysisResult", back_populates="job", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="job")
    company = relationship("Company")
    product = relationship("Product")


class AnalysisResult(Base):
    """Individual stage result within an analysis job (Phase2 pipeline stages)."""

    __tablename__ = "analysis_results"
    __table_args__ = {"schema": "phase2"}

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.analysis_jobs.id"), nullable=False
    )
    stage: str = Column(String(50), nullable=False)  # e.g., '10_claim_element_extractor'
    input_data: Optional[dict] = Column(JSON)
    output_data: Optional[dict] = Column(JSON)
    llm_model: Optional[str] = Column(String(50))
    tokens_input: Optional[int] = Column(Integer)
    tokens_output: Optional[int] = Column(Integer)
    latency_ms: Optional[int] = Column(Integer)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    job = relationship("AnalysisJob", back_populates="results")


class AnalysisRun(Base):
    """Individual analysis execution (from Phase1)."""

    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("idx_analysis_runs_job", "job_id"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.analysis_jobs.id")
    )
    document_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.documents.id")
    )
    claim_id: Optional[uuid.UUID] = Column(
        UUID(as_uuid=True), ForeignKey("phase2.claims.id")
    )
    model: Optional[str] = Column(Text)
    ruleset_version: Optional[str] = Column(Text)
    raw_output: Optional[dict] = Column(JSON)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    job = relationship("AnalysisJob", back_populates="runs")
    document = relationship("Document", back_populates="analysis_runs")
    claim = relationship("Claim", back_populates="analysis_runs")
    assessments = relationship("ElementAssessment", back_populates="analysis_run")


# =============================================================================
# ELEMENT ASSESSMENT (From Phase1)
# =============================================================================

class ElementAssessment(Base):
    """Assessment of a claim element against a product version."""

    __tablename__ = "element_assessments"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id", "claim_element_id", "product_version_id",
            name="uq_element_assessments_run_element_version"
        ),
        Index("idx_element_assessments_status", "status"),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.analysis_runs.id"), nullable=False
    )
    claim_element_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.claim_elements.id"), nullable=False
    )
    product_version_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.product_versions.id"), nullable=False
    )
    status: str = Column(Text, nullable=False)  # 'met', 'not_met', 'uncertain'
    confidence: Optional[float] = Column(Float)
    rationale: Optional[str] = Column(Text)
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=utcnow)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="assessments")
    claim_element = relationship("ClaimElement", back_populates="assessments")
    product_version = relationship("ProductVersion", back_populates="assessments")
    evidence_links = relationship("ElementAssessmentEvidence", back_populates="assessment", cascade="all, delete-orphan")


class ElementAssessmentEvidence(Base):
    """Link between assessment and evidence."""

    __tablename__ = "element_assessment_evidence"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id", "evidence_id",
            name="uq_element_assessment_evidence_assessment_evidence"
        ),
        {"schema": "phase2"},
    )

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.element_assessments.id"), nullable=False
    )
    evidence_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("phase2.evidence.id"), nullable=False
    )
    created_at: datetime = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    assessment = relationship("ElementAssessment", back_populates="evidence_links")
    evidence = relationship("Evidence", back_populates="assessment_links")
