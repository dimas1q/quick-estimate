"""add default workspace reference for users

Revision ID: b9d0e1f2a3b4
Revises: a8b9c0d1e2f3
Create Date: 2026-03-13 15:05:00.000000
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9d0e1f2a3b4"
down_revision: Union[str, None] = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("default_organization_id", sa.Integer(), nullable=True))
    op.create_index(
        "ix_users_default_organization_id",
        "users",
        ["default_organization_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_users_default_organization_id",
        "users",
        "organizations",
        ["default_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        UPDATE users
        SET default_organization_id = current_organization_id
        WHERE default_organization_id IS NULL
          AND current_organization_id IS NOT NULL
        """
    )
    op.execute(
        """
        WITH first_membership AS (
            SELECT DISTINCT ON (om.user_id)
                om.user_id,
                om.organization_id
            FROM organization_memberships AS om
            ORDER BY om.user_id, om.created_at ASC, om.id ASC
        )
        UPDATE users AS u
        SET default_organization_id = fm.organization_id
        FROM first_membership AS fm
        WHERE u.id = fm.user_id
          AND u.default_organization_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_default_organization_id", "users", type_="foreignkey")
    op.drop_index("ix_users_default_organization_id", table_name="users")
    op.drop_column("users", "default_organization_id")

