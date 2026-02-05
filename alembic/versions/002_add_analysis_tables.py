"""Add analysis tables.

Revision ID: 002
Revises: 001
Create Date: 2025-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # analysis_jobs table
    op.create_table(
        "analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patent_id", sa.String(30), nullable=False),
        sa.Column("target_product", sa.Text),
        sa.Column("pipeline", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("current_stage", sa.String(50)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("context_json", postgresql.JSONB),
        schema="phase2",
    )

    # analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phase2.analysis_jobs.id"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("input_data", postgresql.JSONB),
        sa.Column("output_data", postgresql.JSONB),
        sa.Column("llm_model", sa.String(50)),
        sa.Column("tokens_input", sa.Integer),
        sa.Column("tokens_output", sa.Integer),
        sa.Column("latency_ms", sa.Integer),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        schema="phase2",
    )

    # Indexes
    op.create_index(
        "ix_analysis_jobs_patent_id",
        "analysis_jobs",
        ["patent_id"],
        schema="phase2",
    )
    op.create_index(
        "ix_analysis_jobs_status",
        "analysis_jobs",
        ["status"],
        schema="phase2",
    )
    op.create_index(
        "ix_analysis_results_job_id",
        "analysis_results",
        ["job_id"],
        schema="phase2",
    )


def downgrade() -> None:
    op.drop_table("analysis_results", schema="phase2")
    op.drop_table("analysis_jobs", schema="phase2")
