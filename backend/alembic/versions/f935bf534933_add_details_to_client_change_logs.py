"""add details to client_change_logs

Revision ID: f935bf534933
Revises: 8087ed1d81b4
Create Date: 2025-06-09 16:04:54.951971

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f935bf534933"
down_revision: Union[str, None] = "8087ed1d81b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    from sqlalchemy import JSON

    op.add_column("client_change_logs", sa.Column("details", JSON(), nullable=True))


def downgrade():
    op.drop_column("client_change_logs", "details")
