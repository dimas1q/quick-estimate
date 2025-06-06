"""add client change logs table

Revision ID: f54c133b
Revises: c4c7786c8937
Create Date: 2025-06-01 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f54c133b"
down_revision: Union[str, None] = "c4c7786c8937"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_change_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE")
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("client_change_logs")
