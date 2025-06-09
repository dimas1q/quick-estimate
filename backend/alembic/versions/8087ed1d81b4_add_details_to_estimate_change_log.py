"""add details to estimate_change_log

Revision ID: 8087ed1d81b4
Revises: a1b2c3d4e5f6
Create Date: 2025-06-09 09:30:31.350654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8087ed1d81b4'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('estimate_change_logs', sa.Column('details', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('estimate_change_logs', 'details')
