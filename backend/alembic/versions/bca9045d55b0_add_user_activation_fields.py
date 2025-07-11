"""add user activation fields"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'bca9045d55b0'
down_revision: Union[str, None] = 'fb212cb36ab6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('hashed_otp', sa.String(), nullable=True))
    op.add_column('users', sa.Column('otp_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('otp_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.alter_column('users', 'is_active', server_default='0')


def downgrade() -> None:
    op.drop_column('users', 'otp_sent_at')
    op.drop_column('users', 'otp_expires_at')
    op.drop_column('users', 'hashed_otp')
    op.drop_column('users', 'is_active')
