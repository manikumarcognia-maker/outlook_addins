"""thread_messages source_message_id for conversation sync

Revision ID: e7f8a9b0c1d2
Revises: d4e5f6a7b8c9
Create Date: 2026-10-03 18:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "thread_messages",
        sa.Column("source_message_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "uq_thread_messages_thread_source_message_id",
        "thread_messages",
        ["thread_id", "source_message_id"],
        unique=True,
        postgresql_where=sa.text("source_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_thread_messages_thread_source_message_id",
        table_name="thread_messages",
    )
    op.drop_column("thread_messages", "source_message_id")
