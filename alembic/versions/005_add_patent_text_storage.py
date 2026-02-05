"""Add patent text storage tables and raw file metadata.

Revision ID: 005
Revises: 004
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend raw_files for Supabase Storage metadata
    op.add_column(
        "raw_files",
        sa.Column("storage_provider", sa.String(20)),
        schema="phase2",
    )
    op.add_column(
        "raw_files",
        sa.Column("bucket", sa.String(100)),
        schema="phase2",
    )
    op.add_column(
        "raw_files",
        sa.Column("object_path", sa.Text()),
        schema="phase2",
    )
    op.add_column(
        "raw_files",
        sa.Column("mime_type", sa.String(100)),
        schema="phase2",
    )
    op.add_column(
        "raw_files",
        sa.Column("size_bytes", sa.BigInteger()),
        schema="phase2",
    )
    op.add_column(
        "raw_files",
        sa.Column("etag", sa.String(100)),
        schema="phase2",
    )

    # patents
    op.create_table(
        "patents",
        sa.Column("internal_patent_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jurisdiction", sa.String(2), nullable=False, server_default="JP"),
        sa.Column("application_no", sa.String(40)),
        sa.Column("publication_no", sa.String(40)),
        sa.Column("registration_no", sa.String(40)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        schema="phase2",
    )
    op.create_index(
        "uq_patents_application_no",
        "patents",
        ["jurisdiction", "application_no"],
        unique=True,
        schema="phase2",
        postgresql_where=sa.text("application_no IS NOT NULL"),
    )
    op.create_index(
        "uq_patents_publication_no",
        "patents",
        ["jurisdiction", "publication_no"],
        unique=True,
        schema="phase2",
        postgresql_where=sa.text("publication_no IS NOT NULL"),
    )
    op.create_index(
        "uq_patents_registration_no",
        "patents",
        ["jurisdiction", "registration_no"],
        unique=True,
        schema="phase2",
        postgresql_where=sa.text("registration_no IS NOT NULL"),
    )

    # patent_number_sources
    op.create_table(
        "patent_number_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "internal_patent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.patents.internal_patent_id"),
            nullable=False,
        ),
        sa.Column("number_type", sa.String(20), nullable=False),
        sa.Column("number_value_raw", sa.Text(), nullable=False),
        sa.Column("number_value_norm", sa.Text()),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_ref", sa.Text()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("confidence", sa.Float()),
        schema="phase2",
    )
    op.create_index(
        "uq_patent_number_sources",
        "patent_number_sources",
        ["internal_patent_id", "number_type", "number_value_raw", "source_type"],
        unique=True,
        schema="phase2",
    )
    op.create_index(
        "idx_patent_number_sources_patent",
        "patent_number_sources",
        ["internal_patent_id"],
        schema="phase2",
    )

    # patent_versions
    op.create_table(
        "patent_versions",
        sa.Column("version_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "internal_patent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.patents.internal_patent_id"),
            nullable=False,
        ),
        sa.Column("publication_type", sa.String(20), nullable=False),
        sa.Column("kind_code", sa.String(10)),
        sa.Column("gazette_number", sa.String(40)),
        sa.Column("issue_date", sa.Date()),
        sa.Column("language", sa.String(8), server_default="ja"),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_ref", sa.Text()),
        sa.Column(
            "raw_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.raw_files.id"),
        ),
        sa.Column("raw_object_uri", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("parse_status", sa.String(20)),
        sa.Column("parse_result_json", postgresql.JSONB),
        sa.Column("norm_version", sa.String(20)),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("acquired_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="phase2",
    )
    op.create_index(
        "uq_patent_versions_hash",
        "patent_versions",
        ["internal_patent_id", "publication_type", "content_hash"],
        unique=True,
        schema="phase2",
        postgresql_where=sa.text("content_hash IS NOT NULL"),
    )
    op.create_index(
        "uq_patent_versions_latest",
        "patent_versions",
        ["internal_patent_id", "publication_type"],
        unique=True,
        schema="phase2",
        postgresql_where=sa.text("is_latest IS TRUE"),
    )
    op.create_index(
        "idx_patent_versions_internal",
        "patent_versions",
        ["internal_patent_id"],
        schema="phase2",
    )

    # patent_claims
    op.create_table(
        "patent_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.patent_versions.version_id"),
            nullable=False,
        ),
        sa.Column("claim_no", sa.Integer, nullable=False),
        sa.Column("text_raw", sa.Text(), nullable=False),
        sa.Column("text_norm", sa.Text()),
        sa.Column("norm_version", sa.String(20)),
        schema="phase2",
    )
    op.create_index(
        "uq_patent_claims_version_claim_no",
        "patent_claims",
        ["version_id", "claim_no"],
        unique=True,
        schema="phase2",
    )
    op.create_index(
        "idx_patent_claims_version",
        "patent_claims",
        ["version_id"],
        schema="phase2",
    )

    # patent_spec_sections
    op.create_table(
        "patent_spec_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.patent_versions.version_id"),
            nullable=False,
        ),
        sa.Column("section_type", sa.String(40), nullable=False),
        sa.Column("order_no", sa.Integer, nullable=False),
        sa.Column("text_raw", sa.Text(), nullable=False),
        sa.Column("text_norm", sa.Text()),
        sa.Column("norm_version", sa.String(20)),
        schema="phase2",
    )
    op.create_index(
        "uq_patent_spec_sections_version_section_order",
        "patent_spec_sections",
        ["version_id", "section_type", "order_no"],
        unique=True,
        schema="phase2",
    )
    op.create_index(
        "idx_patent_spec_sections_version",
        "patent_spec_sections",
        ["version_id"],
        schema="phase2",
    )

    # ingestion_jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        sa.Column("force_refresh", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_preference", sa.String(20)),
        sa.Column("idempotency_key", sa.String(80), unique=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("error_code", sa.String(50)),
        sa.Column("error_detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        schema="phase2",
    )
    op.create_index(
        "idx_ingestion_jobs_status",
        "ingestion_jobs",
        ["status"],
        schema="phase2",
    )
    op.create_index(
        "idx_ingestion_jobs_created_at",
        "ingestion_jobs",
        ["created_at"],
        schema="phase2",
    )

    # ingestion_job_items
    op.create_table(
        "ingestion_job_items",
        sa.Column("job_item_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.ingestion_jobs.job_id"),
            nullable=False,
        ),
        sa.Column(
            "internal_patent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.patents.internal_patent_id"),
        ),
        sa.Column("input_number", sa.Text(), nullable=False),
        sa.Column("input_number_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(50)),
        sa.Column("error_detail", sa.Text()),
        sa.Column("target_version_hint", postgresql.JSONB),
        schema="phase2",
    )
    op.create_index(
        "uq_ingestion_job_items",
        "ingestion_job_items",
        ["job_id", "input_number", "input_number_type"],
        unique=True,
        schema="phase2",
    )
    op.create_index(
        "idx_ingestion_job_items_job",
        "ingestion_job_items",
        ["job_id"],
        schema="phase2",
    )


def downgrade() -> None:
    op.drop_index("idx_ingestion_job_items_job", table_name="ingestion_job_items", schema="phase2")
    op.drop_index("uq_ingestion_job_items", table_name="ingestion_job_items", schema="phase2")
    op.drop_table("ingestion_job_items", schema="phase2")

    op.drop_index("idx_ingestion_jobs_created_at", table_name="ingestion_jobs", schema="phase2")
    op.drop_index("idx_ingestion_jobs_status", table_name="ingestion_jobs", schema="phase2")
    op.drop_table("ingestion_jobs", schema="phase2")

    op.drop_index(
        "idx_patent_spec_sections_version",
        table_name="patent_spec_sections",
        schema="phase2",
    )
    op.drop_index(
        "uq_patent_spec_sections_version_section_order",
        table_name="patent_spec_sections",
        schema="phase2",
    )
    op.drop_table("patent_spec_sections", schema="phase2")

    op.drop_index("idx_patent_claims_version", table_name="patent_claims", schema="phase2")
    op.drop_index(
        "uq_patent_claims_version_claim_no",
        table_name="patent_claims",
        schema="phase2",
    )
    op.drop_table("patent_claims", schema="phase2")

    op.drop_index("idx_patent_versions_internal", table_name="patent_versions", schema="phase2")
    op.drop_index("uq_patent_versions_latest", table_name="patent_versions", schema="phase2")
    op.drop_index("uq_patent_versions_hash", table_name="patent_versions", schema="phase2")
    op.drop_table("patent_versions", schema="phase2")

    op.drop_index("idx_patent_number_sources_patent", table_name="patent_number_sources", schema="phase2")
    op.drop_index("uq_patent_number_sources", table_name="patent_number_sources", schema="phase2")
    op.drop_table("patent_number_sources", schema="phase2")

    op.drop_index("uq_patents_registration_no", table_name="patents", schema="phase2")
    op.drop_index("uq_patents_publication_no", table_name="patents", schema="phase2")
    op.drop_index("uq_patents_application_no", table_name="patents", schema="phase2")
    op.drop_table("patents", schema="phase2")

    op.drop_column("raw_files", "etag", schema="phase2")
    op.drop_column("raw_files", "size_bytes", schema="phase2")
    op.drop_column("raw_files", "mime_type", schema="phase2")
    op.drop_column("raw_files", "object_path", schema="phase2")
    op.drop_column("raw_files", "bucket", schema="phase2")
    op.drop_column("raw_files", "storage_provider", schema="phase2")
