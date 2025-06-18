"""add notes table"

Revision ID: abc123456789
Revises: fb212cb36ab6
Create Date: 2025-07-01 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'abc123456789'
down_revision: Union[str, None] = 'fb212cb36ab6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('estimate_id', sa.Integer(), sa.ForeignKey('estimates.id', ondelete='CASCADE'), nullable=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('estimate_templates.id', ondelete='CASCADE'), nullable=True),
    )
    with op.batch_alter_table('estimates') as batch_op:
        batch_op.drop_column('notes')
    with op.batch_alter_table('clients') as batch_op:
        batch_op.drop_column('notes')
    with op.batch_alter_table('estimate_templates') as batch_op:
        batch_op.drop_column('notes')


def downgrade() -> None:
    op.add_column('estimate_templates', sa.Column('notes', sa.TEXT(), nullable=True))
    op.add_column('clients', sa.Column('notes', sa.TEXT(), nullable=True))
    op.add_column('estimates', sa.Column('notes', sa.TEXT(), nullable=True))
    op.drop_table('notes')
