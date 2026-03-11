"""add read_only flag to estimates

Revision ID: b1c2d3e4f5a6
Revises: c9f8e7d6b5a4
Create Date: 2026-03-12 04:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "c9f8e7d6b5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("estimates")}

    if "read_only" not in columns:
        op.add_column(
            "estimates",
            sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("estimates", "read_only", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("estimates")}

    if "read_only" in columns:
        op.drop_column("estimates", "read_only")
