"""add login lock fields to users

Revision ID: c9f8e7d6b5a4
Revises: e1a2b3c4d5e6
Create Date: 2026-03-12 03:50:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9f8e7d6b5a4"
down_revision: Union[str, None] = "e1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "failed_login_attempts" not in columns:
        op.add_column(
            "users",
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("users", "failed_login_attempts", server_default=None)

    if "locked_until" not in columns:
        op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "locked_until" in columns:
        op.drop_column("users", "locked_until")

    if "failed_login_attempts" in columns:
        op.drop_column("users", "failed_login_attempts")
