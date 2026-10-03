"""drafts source_message_id for inbound dedupe

Revision ID: d4e5f6a7b8c9
Revises: c8f2a1b3d4e5
Create Date: 2026-10-03 14:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c8f2a1b3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drafts", sa.Column("source_message_id", sa.Text(), nullable=True))
    op.create_index(
        "uq_drafts_thread_source_message_id",
        "drafts",
        ["thread_id", "source_message_id"],
        unique=True,
        postgresql_where=sa.text("source_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_drafts_thread_source_message_id", table_name="drafts")
    op.drop_column("drafts", "source_message_id")
