"""add use_internal_price option

Revision ID: 0123456789ab
Revises: fb212cb36ab6
Create Date: 2025-07-01 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0123456789ab"
down_revision: Union[str, None] = "abc123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "estimates",
        sa.Column(
            "use_internal_price", sa.Boolean(), nullable=False, server_default="1"
        ),
    )
    op.add_column(
        "estimate_templates",
        sa.Column(
            "use_internal_price", sa.Boolean(), nullable=False, server_default="1"
        ),
    )
    op.alter_column("estimates", "use_internal_price", server_default=None)
    op.alter_column("estimate_templates", "use_internal_price", server_default=None)


def downgrade() -> None:
    op.drop_column("estimate_templates", "use_internal_price")
    op.drop_column("estimates", "use_internal_price")
