"""email agent drafts table

Revision ID: c8f2a1b3d4e5
Revises: 5bab1b841d97
Create Date: 2026-10-03 14:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c8f2a1b3d4e5"
down_revision: Union[str, Sequence[str], None] = "5bab1b841d97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "thread_id",
            sa.Text(),
            sa.ForeignKey("threads.thread_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("draft_body", sa.Text(), nullable=False),
        sa.Column("retrieval_status", sa.Text(), nullable=False),
        sa.Column(
            "citations",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'pending_review'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "retrieval_status IN ('success', 'empty', 'error')",
            name="ck_drafts_retrieval_status",
        ),
        sa.CheckConstraint(
            "status IN ('pending_review', 'approved', 'edited_and_approved')",
            name="ck_drafts_status",
        ),
    )
    op.create_index(
        "idx_drafts_thread_status",
        "drafts",
        ["thread_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_drafts_thread_status", table_name="drafts")
    op.drop_table("drafts")
