"""add organizations and memberships

Revision ID: f6a7b8c9d0e1
Revises: e7f8a9b0c1d2
Create Date: 2026-03-13 09:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("domain", sa.String(length=120), nullable=True),
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
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
        sa.UniqueConstraint("domain", name="uq_organizations_domain"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=False)
    op.create_index("ix_organizations_domain", "organizations", ["domain"], unique=False)

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_membership",
        ),
    )
    op.create_index(
        "ix_organization_memberships_organization_id",
        "organization_memberships",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_memberships_user_id",
        "organization_memberships",
        ["user_id"],
        unique=False,
    )

    op.add_column("users", sa.Column("current_organization_id", sa.Integer(), nullable=True))
    op.create_index(
        "ix_users_current_organization_id",
        "users",
        ["current_organization_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_users_current_organization_id",
        "users",
        "organizations",
        ["current_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )

    bind = op.get_bind()
    users = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("login", sa.String),
        sa.column("company", sa.String),
        sa.column("email", sa.String),
        sa.column("current_organization_id", sa.Integer),
    )
    organizations = sa.table(
        "organizations",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("domain", sa.String),
    )
    memberships = sa.table(
        "organization_memberships",
        sa.column("organization_id", sa.Integer),
        sa.column("user_id", sa.Integer),
        sa.column("role", sa.String),
    )

    user_rows = bind.execute(
        sa.select(users.c.id, users.c.login, users.c.company, users.c.email).order_by(users.c.id.asc())
    ).all()
    for row in user_rows:
        user_id = int(row.id)
        login = (row.login or "").strip() or f"user{user_id}"
        company = (row.company or "").strip()
        org_name = company or f"Рабочее пространство {login}"
        org_slug = f"user-{user_id}"

        org_id = bind.execute(
            sa.insert(organizations)
            .values(name=org_name[:120], slug=org_slug, domain=None)
            .returning(organizations.c.id)
        ).scalar_one()

        bind.execute(
            sa.update(users)
            .where(users.c.id == user_id)
            .values(current_organization_id=org_id)
        )
        bind.execute(
            sa.insert(memberships).values(
                organization_id=org_id,
                user_id=user_id,
                role="owner",
            )
        )


def downgrade() -> None:
    op.drop_constraint("fk_users_current_organization_id", "users", type_="foreignkey")
    op.drop_index("ix_users_current_organization_id", table_name="users")
    op.drop_column("users", "current_organization_id")

    op.drop_index("ix_organization_memberships_user_id", table_name="organization_memberships")
    op.drop_index(
        "ix_organization_memberships_organization_id",
        table_name="organization_memberships",
    )
    op.drop_table("organization_memberships")

    op.drop_index("ix_organizations_domain", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
