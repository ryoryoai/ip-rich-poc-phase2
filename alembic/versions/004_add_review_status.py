"""Add review status to link tables.

Revision ID: 004
Revises: 003
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "company_product_links",
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        schema="phase2",
    )
    op.add_column(
        "company_product_links",
        sa.Column("review_note", sa.Text()),
        schema="phase2",
    )

    op.add_column(
        "patent_company_links",
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        schema="phase2",
    )
    op.add_column(
        "patent_company_links",
        sa.Column("review_note", sa.Text()),
        schema="phase2",
    )

    # Backfill: deterministic links are considered approved
    op.execute(
        "UPDATE phase2.company_product_links SET review_status = 'approved' "
        "WHERE link_type = 'deterministic'"
    )
    op.execute(
        "UPDATE phase2.patent_company_links SET review_status = 'approved' "
        "WHERE link_type = 'deterministic'"
    )


def downgrade() -> None:
    op.drop_column("patent_company_links", "review_note", schema="phase2")
    op.drop_column("patent_company_links", "review_status", schema="phase2")
    op.drop_column("company_product_links", "review_note", schema="phase2")
    op.drop_column("company_product_links", "review_status", schema="phase2")
