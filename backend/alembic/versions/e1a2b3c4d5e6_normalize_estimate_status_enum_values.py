"""normalize estimate_status enum values to lowercase

Revision ID: e1a2b3c4d5e6
Revises: d1e2f3a4b5c6
Create Date: 2026-03-12 00:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LOWER_VALUES = ["draft", "sent", "approved", "paid", "cancelled"]
UPPER_VALUES = ["DRAFT", "SENT", "APPROVED", "PAID", "CANCELLED"]


def _get_enum_labels(conn):
    return conn.execute(
        sa.text(
            """
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'estimate_status'
            ORDER BY e.enumsortorder
            """
        )
    ).scalars().all()


def upgrade() -> None:
    conn = op.get_bind()
    labels = _get_enum_labels(conn)
    if not labels:
        return

    # Already normalized.
    if labels == LOWER_VALUES:
        return

    op.execute("ALTER TYPE estimate_status RENAME TO estimate_status_old")
    op.execute(
        "CREATE TYPE estimate_status AS ENUM ('draft','sent','approved','paid','cancelled')"
    )
    op.execute(
        """
        ALTER TABLE estimates
        ALTER COLUMN status
        TYPE estimate_status
        USING (
            CASE
                WHEN status::text IN ('DRAFT', 'draft') THEN 'draft'
                WHEN status::text IN ('SENT', 'sent') THEN 'sent'
                WHEN status::text IN ('APPROVED', 'approved') THEN 'approved'
                WHEN status::text IN ('PAID', 'paid') THEN 'paid'
                WHEN status::text IN ('CANCELLED', 'cancelled') THEN 'cancelled'
                ELSE 'draft'
            END
        )::estimate_status
        """
    )
    op.execute("DROP TYPE estimate_status_old")


def downgrade() -> None:
    conn = op.get_bind()
    labels = _get_enum_labels(conn)
    if not labels:
        return

    if labels == UPPER_VALUES:
        return

    op.execute("ALTER TYPE estimate_status RENAME TO estimate_status_old")
    op.execute(
        "CREATE TYPE estimate_status AS ENUM ('DRAFT','SENT','APPROVED','PAID','CANCELLED')"
    )
    op.execute(
        """
        ALTER TABLE estimates
        ALTER COLUMN status
        TYPE estimate_status
        USING (
            CASE
                WHEN status::text IN ('draft', 'DRAFT') THEN 'DRAFT'
                WHEN status::text IN ('sent', 'SENT') THEN 'SENT'
                WHEN status::text IN ('approved', 'APPROVED') THEN 'APPROVED'
                WHEN status::text IN ('paid', 'PAID') THEN 'PAID'
                WHEN status::text IN ('cancelled', 'CANCELLED') THEN 'CANCELLED'
                ELSE 'DRAFT'
            END
        )::estimate_status
        """
    )
    op.execute("DROP TYPE estimate_status_old")
