"""email thread agent tables

Revision ID: 5bab1b841d97
Revises:
Create Date: 2026-10-03 11:03:49.769868

Recent messages (Phase 2): WHERE thread_id = ? AND is_summarized = false
ORDER BY created_at DESC LIMIT 3
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5bab1b841d97"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "threads",
        sa.Column("thread_id", sa.Text(), primary_key=True),
        sa.Column("customer_id", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "shipment_facts",
        sa.Column(
            "thread_id",
            sa.Text(),
            sa.ForeignKey("threads.thread_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("subject_id", sa.Text(), primary_key=True),
        sa.Column(
            "facts",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "thread_summary",
        sa.Column(
            "thread_id",
            sa.Text(),
            sa.ForeignKey("threads.thread_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "thread_messages",
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
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "is_summarized",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="True once folded into thread_summary; excluded from recent (last 3) queries",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('customer', 'assistant')",
            name="ck_thread_messages_role",
        ),
    )

    op.create_index(
        "idx_thread_messages_recent",
        "thread_messages",
        ["thread_id", "is_summarized", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_thread_messages_recent", table_name="thread_messages")
    op.drop_table("thread_messages")
    op.drop_table("thread_summary")
    op.drop_table("shipment_facts")
    op.drop_table("threads")
