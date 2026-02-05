"""Add document texts, tech keywords, and profile fields.

Revision ID: 005
Revises: 004
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "claims",
        sa.Column("source", sa.String(30)),
        schema="phase2",
    )
    op.add_column(
        "claims",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        schema="phase2",
    )
    op.add_column(
        "claim_elements",
        sa.Column("metadata_json", sa.JSON()),
        schema="phase2",
    )

    op.add_column(
        "companies",
        sa.Column("business_description", sa.Text()),
        schema="phase2",
    )
    op.add_column(
        "companies",
        sa.Column("primary_products", sa.Text()),
        schema="phase2",
    )
    op.add_column(
        "companies",
        sa.Column("market_regions", sa.Text()),
        schema="phase2",
    )

    op.add_column(
        "products",
        sa.Column("brand_name", sa.Text()),
        schema="phase2",
    )

    op.create_table(
        "document_texts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text_type", sa.String(30), nullable=False),
        sa.Column("language", sa.String(8)),
        sa.Column("source", sa.String(30)),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["document_id"], ["phase2.documents.id"]),
        schema="phase2",
    )
    op.create_index(
        "idx_document_texts_document",
        "document_texts",
        ["document_id"],
        schema="phase2",
    )
    op.create_index(
        "idx_document_texts_type",
        "document_texts",
        ["text_type"],
        schema="phase2",
    )
    op.create_index(
        "idx_document_texts_current",
        "document_texts",
        ["document_id", "text_type", "is_current"],
        schema="phase2",
    )

    op.create_table(
        "tech_keywords",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("term", sa.Text(), nullable=False),
        sa.Column("language", sa.String(8), nullable=False, server_default="ja"),
        sa.Column("normalized_term", sa.Text()),
        sa.Column("synonyms", sa.JSON()),
        sa.Column("abbreviations", sa.JSON()),
        sa.Column("domain", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("source_evidence_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["source_evidence_id"], ["phase2.evidence.id"]),
        schema="phase2",
    )
    op.create_index(
        "idx_tech_keywords_term",
        "tech_keywords",
        ["term"],
        schema="phase2",
    )
    op.create_index(
        "idx_tech_keywords_language",
        "tech_keywords",
        ["language"],
        schema="phase2",
    )


def downgrade() -> None:
    op.drop_index("idx_tech_keywords_language", table_name="tech_keywords", schema="phase2")
    op.drop_index("idx_tech_keywords_term", table_name="tech_keywords", schema="phase2")
    op.drop_table("tech_keywords", schema="phase2")

    op.drop_index("idx_document_texts_current", table_name="document_texts", schema="phase2")
    op.drop_index("idx_document_texts_type", table_name="document_texts", schema="phase2")
    op.drop_index("idx_document_texts_document", table_name="document_texts", schema="phase2")
    op.drop_table("document_texts", schema="phase2")

    op.drop_column("products", "brand_name", schema="phase2")
    op.drop_column("companies", "market_regions", schema="phase2")
    op.drop_column("companies", "primary_products", schema="phase2")
    op.drop_column("companies", "business_description", schema="phase2")
    op.drop_column("claim_elements", "metadata_json", schema="phase2")
    op.drop_column("claims", "is_current", schema="phase2")
    op.drop_column("claims", "source", schema="phase2")
