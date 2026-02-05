"""Add company/product master data and link tables.

Revision ID: 003
Revises: 002
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # companies: add master data columns
    op.add_column("companies", sa.Column("corporate_number", sa.String(13)), schema="phase2")
    op.add_column("companies", sa.Column("country", sa.String(2)), schema="phase2")
    op.add_column("companies", sa.Column("legal_type", sa.String(50)), schema="phase2")
    op.add_column("companies", sa.Column("normalized_name", sa.Text()), schema="phase2")
    op.add_column("companies", sa.Column("address_raw", sa.Text()), schema="phase2")
    op.add_column("companies", sa.Column("address_pref", sa.String(20)), schema="phase2")
    op.add_column("companies", sa.Column("address_city", sa.String(50)), schema="phase2")
    op.add_column("companies", sa.Column("status", sa.String(20)), schema="phase2")
    op.add_column("companies", sa.Column("is_listed", sa.Boolean()), schema="phase2")
    op.add_column("companies", sa.Column("has_jp_entity", sa.Boolean()), schema="phase2")
    op.add_column("companies", sa.Column("website_url", sa.Text()), schema="phase2")
    op.add_column("companies", sa.Column("contact_url", sa.Text()), schema="phase2")
    op.create_unique_constraint(
        "uq_companies_corporate_number", "companies", ["corporate_number"], schema="phase2"
    )
    op.create_index(
        "idx_companies_corporate_number", "companies", ["corporate_number"], schema="phase2"
    )
    op.create_index(
        "idx_companies_normalized_name", "companies", ["normalized_name"], schema="phase2"
    )

    # company_aliases: add metadata
    op.add_column("company_aliases", sa.Column("alias_type", sa.String(30)), schema="phase2")
    op.add_column("company_aliases", sa.Column("language", sa.String(8)), schema="phase2")
    op.add_column(
        "company_aliases",
        sa.Column("source_evidence_id", postgresql.UUID(as_uuid=True)),
        schema="phase2",
    )
    op.create_foreign_key(
        "fk_company_aliases_source_evidence",
        "company_aliases",
        "evidence",
        ["source_evidence_id"],
        ["id"],
        source_schema="phase2",
        referent_schema="phase2",
    )
    op.create_index(
        "idx_company_aliases_alias", "company_aliases", ["alias"], schema="phase2"
    )

    # products: add master data columns
    op.add_column("products", sa.Column("model_number", sa.Text()), schema="phase2")
    op.add_column("products", sa.Column("category_path", sa.Text()), schema="phase2")
    op.add_column("products", sa.Column("description", sa.Text()), schema="phase2")
    op.add_column("products", sa.Column("sale_region", sa.Text()), schema="phase2")
    op.add_column("products", sa.Column("normalized_name", sa.Text()), schema="phase2")
    op.add_column("products", sa.Column("status", sa.String(20)), schema="phase2")
    op.create_index(
        "idx_products_model_number", "products", ["model_number"], schema="phase2"
    )
    op.create_index(
        "idx_products_normalized_name", "products", ["normalized_name"], schema="phase2"
    )

    # evidence: add snapshot metadata
    op.add_column("evidence", sa.Column("source_type", sa.String(50)), schema="phase2")
    op.add_column("evidence", sa.Column("captured_at", sa.DateTime(timezone=True)), schema="phase2")
    op.add_column("evidence", sa.Column("content_hash", sa.String(64)), schema="phase2")
    op.add_column("evidence", sa.Column("content_type", sa.String(100)), schema="phase2")
    op.add_column("evidence", sa.Column("storage_path", sa.Text()), schema="phase2")
    op.create_index(
        "idx_evidence_content_hash", "evidence", ["content_hash"], schema="phase2"
    )

    # analysis_jobs: link to company/product
    op.add_column(
        "analysis_jobs",
        sa.Column("company_id", postgresql.UUID(as_uuid=True)),
        schema="phase2",
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("product_id", postgresql.UUID(as_uuid=True)),
        schema="phase2",
    )
    op.create_foreign_key(
        "fk_analysis_jobs_company",
        "analysis_jobs",
        "companies",
        ["company_id"],
        ["id"],
        source_schema="phase2",
        referent_schema="phase2",
    )
    op.create_foreign_key(
        "fk_analysis_jobs_product",
        "analysis_jobs",
        "products",
        ["product_id"],
        ["id"],
        source_schema="phase2",
        referent_schema="phase2",
    )
    op.create_index(
        "idx_analysis_jobs_company_id", "analysis_jobs", ["company_id"], schema="phase2"
    )
    op.create_index(
        "idx_analysis_jobs_product_id", "analysis_jobs", ["product_id"], schema="phase2"
    )

    # company_identifiers
    op.create_table(
        "company_identifiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.companies.id"),
            nullable=False,
        ),
        sa.Column("id_type", sa.String(30), nullable=False),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column(
            "source_evidence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.evidence.id"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "company_id", "id_type", "value", name="uq_company_identifiers"
        ),
        schema="phase2",
    )
    op.create_index(
        "idx_company_identifiers_value", "company_identifiers", ["value"], schema="phase2"
    )

    # product_identifiers
    op.create_table(
        "product_identifiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.products.id"),
            nullable=False,
        ),
        sa.Column("id_type", sa.String(30), nullable=False),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column(
            "source_evidence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.evidence.id"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "product_id", "id_type", "value", name="uq_product_identifiers"
        ),
        schema="phase2",
    )
    op.create_index(
        "idx_product_identifiers_value", "product_identifiers", ["value"], schema="phase2"
    )

    # company_evidence_links
    op.create_table(
        "company_evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.companies.id"),
            nullable=False,
        ),
        sa.Column(
            "evidence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.evidence.id"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "company_id", "evidence_id", "purpose", name="uq_company_evidence_links"
        ),
        schema="phase2",
    )
    op.create_index(
        "idx_company_evidence_links_company",
        "company_evidence_links",
        ["company_id"],
        schema="phase2",
    )

    # product_evidence_links
    op.create_table(
        "product_evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.products.id"),
            nullable=False,
        ),
        sa.Column(
            "product_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.product_versions.id"),
        ),
        sa.Column(
            "evidence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.evidence.id"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "product_id",
            "product_version_id",
            "evidence_id",
            name="uq_product_evidence_links",
        ),
        schema="phase2",
    )
    op.create_index(
        "idx_product_evidence_links_product",
        "product_evidence_links",
        ["product_id"],
        schema="phase2",
    )

    # company_product_links
    op.create_table(
        "company_product_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.companies.id"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.products.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("link_type", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("evidence_json", postgresql.JSONB),
        sa.Column("verified_by", sa.Text()),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "company_id",
            "product_id",
            "role",
            name="uq_company_product_links_company_product_role",
        ),
        schema="phase2",
    )
    op.create_index(
        "idx_company_product_links_company",
        "company_product_links",
        ["company_id"],
        schema="phase2",
    )
    op.create_index(
        "idx_company_product_links_product",
        "company_product_links",
        ["product_id"],
        schema="phase2",
    )

    # patent_company_links
    op.create_table(
        "patent_company_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.documents.id"),
        ),
        sa.Column("patent_ref", sa.String(40)),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.companies.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("link_type", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("evidence_json", postgresql.JSONB),
        sa.Column("verified_by", sa.Text()),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "document_id",
            "patent_ref",
            "company_id",
            "role",
            name="uq_patent_company_links_doc_patent_company_role",
        ),
        schema="phase2",
    )
    op.create_index(
        "idx_patent_company_links_company",
        "patent_company_links",
        ["company_id"],
        schema="phase2",
    )
    op.create_index(
        "idx_patent_company_links_document",
        "patent_company_links",
        ["document_id"],
        schema="phase2",
    )


def downgrade() -> None:
    op.drop_index("idx_patent_company_links_document", table_name="patent_company_links", schema="phase2")
    op.drop_index("idx_patent_company_links_company", table_name="patent_company_links", schema="phase2")
    op.drop_table("patent_company_links", schema="phase2")

    op.drop_index("idx_company_product_links_product", table_name="company_product_links", schema="phase2")
    op.drop_index("idx_company_product_links_company", table_name="company_product_links", schema="phase2")
    op.drop_table("company_product_links", schema="phase2")

    op.drop_index("idx_product_evidence_links_product", table_name="product_evidence_links", schema="phase2")
    op.drop_table("product_evidence_links", schema="phase2")

    op.drop_index("idx_company_evidence_links_company", table_name="company_evidence_links", schema="phase2")
    op.drop_table("company_evidence_links", schema="phase2")

    op.drop_index("idx_product_identifiers_value", table_name="product_identifiers", schema="phase2")
    op.drop_table("product_identifiers", schema="phase2")

    op.drop_index("idx_company_identifiers_value", table_name="company_identifiers", schema="phase2")
    op.drop_table("company_identifiers", schema="phase2")

    op.drop_index("idx_analysis_jobs_product_id", table_name="analysis_jobs", schema="phase2")
    op.drop_index("idx_analysis_jobs_company_id", table_name="analysis_jobs", schema="phase2")
    op.drop_constraint("fk_analysis_jobs_product", "analysis_jobs", schema="phase2", type_="foreignkey")
    op.drop_constraint("fk_analysis_jobs_company", "analysis_jobs", schema="phase2", type_="foreignkey")
    op.drop_column("analysis_jobs", "product_id", schema="phase2")
    op.drop_column("analysis_jobs", "company_id", schema="phase2")

    op.drop_index("idx_evidence_content_hash", table_name="evidence", schema="phase2")
    op.drop_column("evidence", "storage_path", schema="phase2")
    op.drop_column("evidence", "content_type", schema="phase2")
    op.drop_column("evidence", "content_hash", schema="phase2")
    op.drop_column("evidence", "captured_at", schema="phase2")
    op.drop_column("evidence", "source_type", schema="phase2")

    op.drop_index("idx_products_normalized_name", table_name="products", schema="phase2")
    op.drop_index("idx_products_model_number", table_name="products", schema="phase2")
    op.drop_column("products", "status", schema="phase2")
    op.drop_column("products", "normalized_name", schema="phase2")
    op.drop_column("products", "sale_region", schema="phase2")
    op.drop_column("products", "description", schema="phase2")
    op.drop_column("products", "category_path", schema="phase2")
    op.drop_column("products", "model_number", schema="phase2")

    op.drop_index("idx_company_aliases_alias", table_name="company_aliases", schema="phase2")
    op.drop_constraint("fk_company_aliases_source_evidence", "company_aliases", schema="phase2", type_="foreignkey")
    op.drop_column("company_aliases", "source_evidence_id", schema="phase2")
    op.drop_column("company_aliases", "language", schema="phase2")
    op.drop_column("company_aliases", "alias_type", schema="phase2")

    op.drop_index("idx_companies_normalized_name", table_name="companies", schema="phase2")
    op.drop_index("idx_companies_corporate_number", table_name="companies", schema="phase2")
    op.drop_constraint("uq_companies_corporate_number", "companies", schema="phase2", type_="unique")
    op.drop_column("companies", "contact_url", schema="phase2")
    op.drop_column("companies", "website_url", schema="phase2")
    op.drop_column("companies", "has_jp_entity", schema="phase2")
    op.drop_column("companies", "is_listed", schema="phase2")
    op.drop_column("companies", "status", schema="phase2")
    op.drop_column("companies", "address_city", schema="phase2")
    op.drop_column("companies", "address_pref", schema="phase2")
    op.drop_column("companies", "address_raw", schema="phase2")
    op.drop_column("companies", "normalized_name", schema="phase2")
    op.drop_column("companies", "legal_type", schema="phase2")
    op.drop_column("companies", "country", schema="phase2")
    op.drop_column("companies", "corporate_number", schema="phase2")
