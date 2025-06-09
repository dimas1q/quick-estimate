"""add client logs and user in estimate logs

Revision ID: a1b2c3d4e5f6
Revises: 2c80576360cc
Create Date: 2025-06-10 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2c80576360cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # --- 1. Добавляем user_id только если его нет ---
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("estimate_change_logs")]
    if "user_id" not in columns:
        op.add_column('estimate_change_logs', sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'))
        op.create_foreign_key(
            'estimate_change_logs_user_id_fkey',
            'estimate_change_logs', 'users',
            ['user_id'], ['id']
        )
        op.alter_column('estimate_change_logs', 'user_id', server_default=None)

    # --- 2. Создаём client_change_logs только если её нет ---
    tables = inspector.get_table_names()
    if 'client_change_logs' not in tables:
        op.create_table(
            'client_change_logs',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id', ondelete='CASCADE')),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('action', sa.String()),
            sa.Column('description', sa.Text()),
            sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        )

def downgrade() -> None:
    # Откат без проверки существования — если не уверен, добавь аналогичную проверку
    op.drop_table('client_change_logs')
    op.drop_column('estimate_change_logs', 'user_id')
