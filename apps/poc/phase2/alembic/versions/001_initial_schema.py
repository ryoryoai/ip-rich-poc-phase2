"""Initial schema for phase2.

Revision ID: 001
Revises:
Create Date: 2025-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS phase2")

    # raw_files table
    op.create_table(
        "raw_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), unique=True, nullable=False),
        sa.Column("stored_path", sa.Text, nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", postgresql.JSONB),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        schema="phase2",
    )

    # documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("doc_number", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(10)),
        sa.Column("publication_date", sa.Date),
        sa.Column(
            "raw_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.raw_files.id"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "country", "doc_number", "kind", name="uq_documents_country_number_kind"
        ),
        schema="phase2",
    )

    # claims table
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.documents.id"),
            nullable=False,
        ),
        sa.Column("claim_no", sa.Integer, nullable=False),
        sa.Column("claim_text", sa.Text, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "document_id", "claim_no", name="uq_claims_document_claim_no"
        ),
        schema="phase2",
    )

    # ingest_runs table
    op.create_table(
        "ingest_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_type", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("detail_json", postgresql.JSONB),
        schema="phase2",
    )

    # Indexes for common queries
    op.create_index(
        "ix_documents_country_doc_number",
        "documents",
        ["country", "doc_number"],
        schema="phase2",
    )
    op.create_index(
        "ix_claims_document_id",
        "claims",
        ["document_id"],
        schema="phase2",
    )


def downgrade() -> None:
    op.drop_table("claims", schema="phase2")
    op.drop_table("documents", schema="phase2")
    op.drop_table("raw_files", schema="phase2")
    op.drop_table("ingest_runs", schema="phase2")
    op.execute("DROP SCHEMA IF EXISTS phase2")
