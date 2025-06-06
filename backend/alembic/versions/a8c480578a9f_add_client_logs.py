"""add client logs

Revision ID: a8c480578a9f
Revises: 2c80576360cc
Create Date: 2025-06-06 09:35:23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a8c480578a9f'
down_revision: Union[str, None] = '2c80576360cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'client_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('estimate_id', sa.Integer(), sa.ForeignKey('estimates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('client_logs')
