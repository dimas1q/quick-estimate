"""bootstrap default admin user

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-12 05:55:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_ADMIN_LOGIN = "admin"
DEFAULT_ADMIN_EMAIL = "admin@quickestimate.app"
DEFAULT_ADMIN_PASSWORD = "admin12345"
LEGACY_ADMIN_EMAIL = "admin@quickestimate.local"


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "is_admin" not in columns:
        return

    # Keep regular registrations as non-admin by default.
    op.alter_column(
        "users",
        "is_admin",
        existing_type=sa.Boolean(),
        server_default=sa.text("false"),
        existing_nullable=True,
    )

    row = conn.execute(
        sa.text(
            """
            SELECT id, is_admin, is_active
            FROM users
            WHERE email = :email OR login = :login
            ORDER BY id ASC
            LIMIT 1
            """
        ),
        {"email": DEFAULT_ADMIN_EMAIL, "login": DEFAULT_ADMIN_LOGIN},
    ).mappings().first()

    if row:
        conn.execute(
            sa.text(
                """
                UPDATE users
                SET is_admin = true,
                    is_active = true,
                    email = CASE
                        WHEN email = :legacy_email THEN :new_email
                        ELSE email
                    END,
                    failed_login_attempts = COALESCE(failed_login_attempts, 0)
                WHERE id = :id
                """
            ),
            {"id": row["id"], "legacy_email": LEGACY_ADMIN_EMAIL, "new_email": DEFAULT_ADMIN_EMAIL},
        )
        return

    import bcrypt

    password_hash = bcrypt.hashpw(
        DEFAULT_ADMIN_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    conn.execute(
        sa.text(
            """
            INSERT INTO users (
                email,
                login,
                name,
                company,
                hashed_password,
                is_admin,
                is_active,
                failed_login_attempts
            )
            VALUES (
                :email,
                :login,
                :name,
                :company,
                :hashed_password,
                true,
                true,
                0
            )
            """
        ),
        {
            "email": DEFAULT_ADMIN_EMAIL,
            "login": DEFAULT_ADMIN_LOGIN,
            "name": "Admin user",
            "company": "QuickEstimate",
            "hashed_password": password_hash,
        },
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "is_admin",
        existing_type=sa.Boolean(),
        server_default=sa.text("false"),
        existing_nullable=True,
    )
