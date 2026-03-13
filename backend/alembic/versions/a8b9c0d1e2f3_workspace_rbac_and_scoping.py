"""workspace rbac and organization data scoping

Revision ID: a8b9c0d1e2f3
Revises: f6a7b8c9d0e1
Create Date: 2026-03-13 05:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_VALUES = ("owner", "admin", "approver", "estimator", "guest")
INVITE_STATUS_VALUES = ("pending", "accepted", "revoked", "expired")


def upgrade() -> None:
    # Normalize current organization reference where possible.
    op.execute(
        """
        UPDATE users AS u
        SET current_organization_id = m.organization_id
        FROM organization_memberships AS m
        WHERE u.current_organization_id IS NULL
          AND m.user_id = u.id
        """
    )

    # Add workspace scope columns to business entities.
    op.add_column("clients", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("estimate_templates", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("estimates", sa.Column("organization_id", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE clients AS c
        SET organization_id = u.current_organization_id
        FROM users AS u
        WHERE c.organization_id IS NULL
          AND c.user_id = u.id
        """
    )
    op.execute(
        """
        UPDATE estimate_templates AS t
        SET organization_id = u.current_organization_id
        FROM users AS u
        WHERE t.organization_id IS NULL
          AND t.user_id = u.id
        """
    )
    op.execute(
        """
        UPDATE estimates AS e
        SET organization_id = u.current_organization_id
        FROM users AS u
        WHERE e.organization_id IS NULL
          AND e.user_id = u.id
        """
    )

    # Enforce role model in workspace memberships.
    op.execute(
        """
        UPDATE organization_memberships
        SET role = 'estimator'
        WHERE role IS NULL
           OR role = ''
           OR lower(role) = 'member'
        """
    )
    op.execute(
        """
        UPDATE organization_memberships
        SET role = lower(role)
        WHERE role IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE organization_memberships
        SET role = 'estimator'
        WHERE role NOT IN ('owner', 'admin', 'approver', 'estimator', 'guest')
        """
    )

    op.alter_column(
        "organization_memberships",
        "role",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default="estimator",
    )
    op.create_check_constraint(
        "ck_organization_memberships_role",
        "organization_memberships",
        f"role IN {ROLE_VALUES}",
    )
    op.create_index(
        "uq_organization_single_owner",
        "organization_memberships",
        ["organization_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner'"),
    )

    # Enforce org scope constraints.
    op.create_foreign_key(
        "fk_clients_organization_id",
        "clients",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_estimate_templates_organization_id",
        "estimate_templates",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_estimates_organization_id",
        "estimates",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_clients_organization_id", "clients", ["organization_id"], unique=False)
    op.create_index(
        "ix_estimate_templates_organization_id",
        "estimate_templates",
        ["organization_id"],
        unique=False,
    )
    op.create_index("ix_estimates_organization_id", "estimates", ["organization_id"], unique=False)

    op.alter_column("clients", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column(
        "estimate_templates",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column("estimates", "organization_id", existing_type=sa.Integer(), nullable=False)

    # Workspace invitations.
    op.create_table(
        "workspace_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="estimator"),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column(
            "invited_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "accepted_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("token_hash", name="uq_workspace_invitations_token_hash"),
    )
    op.create_index(
        "ix_workspace_invitations_organization_id",
        "workspace_invitations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_workspace_invitations_email",
        "workspace_invitations",
        ["email"],
        unique=False,
    )
    op.create_index(
        "ix_workspace_invitations_pending_email",
        "workspace_invitations",
        ["organization_id", "email"],
        unique=False,
    )
    op.create_index(
        "uq_workspace_invitations_active_email",
        "workspace_invitations",
        ["organization_id", "email"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_check_constraint(
        "ck_workspace_invitations_role",
        "workspace_invitations",
        f"role IN {ROLE_VALUES}",
    )
    op.create_check_constraint(
        "ck_workspace_invitations_status",
        "workspace_invitations",
        f"status IN {INVITE_STATUS_VALUES}",
    )


def downgrade() -> None:
    op.drop_constraint("ck_workspace_invitations_status", "workspace_invitations", type_="check")
    op.drop_constraint("ck_workspace_invitations_role", "workspace_invitations", type_="check")
    op.drop_index("uq_workspace_invitations_active_email", table_name="workspace_invitations")
    op.drop_index("ix_workspace_invitations_pending_email", table_name="workspace_invitations")
    op.drop_index("ix_workspace_invitations_email", table_name="workspace_invitations")
    op.drop_index("ix_workspace_invitations_organization_id", table_name="workspace_invitations")
    op.drop_table("workspace_invitations")

    op.drop_index("uq_organization_single_owner", table_name="organization_memberships")
    op.drop_constraint("ck_organization_memberships_role", "organization_memberships", type_="check")
    op.alter_column(
        "organization_memberships",
        "role",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default="member",
    )

    op.drop_index("ix_estimates_organization_id", table_name="estimates")
    op.drop_index("ix_estimate_templates_organization_id", table_name="estimate_templates")
    op.drop_index("ix_clients_organization_id", table_name="clients")
    op.drop_constraint("fk_estimates_organization_id", "estimates", type_="foreignkey")
    op.drop_constraint(
        "fk_estimate_templates_organization_id",
        "estimate_templates",
        type_="foreignkey",
    )
    op.drop_constraint("fk_clients_organization_id", "clients", type_="foreignkey")

    op.drop_column("estimates", "organization_id")
    op.drop_column("estimate_templates", "organization_id")
    op.drop_column("clients", "organization_id")
