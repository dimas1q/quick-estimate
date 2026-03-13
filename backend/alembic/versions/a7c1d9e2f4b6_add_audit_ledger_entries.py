"""add audit ledger entries

Revision ID: a7c1d9e2f4b6
Revises: f3b7c9d1e2f4
Create Date: 2026-03-13 04:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7c1d9e2f4b6"
down_revision: Union[str, None] = "f3b7c9d1e2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_ledger_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("request_method", sa.String(length=16), nullable=True),
        sa.Column("request_path", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("entry_hash", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("entry_hash", name="uq_audit_ledger_entry_hash"),
    )

    op.create_index("ix_audit_ledger_entries_id", "audit_ledger_entries", ["id"], unique=False)
    op.create_index("ix_audit_ledger_entries_action", "audit_ledger_entries", ["action"], unique=False)
    op.create_index("ix_audit_ledger_entries_entity_type", "audit_ledger_entries", ["entity_type"], unique=False)
    op.create_index("ix_audit_ledger_entries_entity_id", "audit_ledger_entries", ["entity_id"], unique=False)

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_audit_ledger_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'audit_ledger_entries is append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_audit_ledger_no_update
            BEFORE UPDATE ON audit_ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_ledger_mutation();
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_audit_ledger_no_delete
            BEFORE DELETE ON audit_ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_ledger_mutation();
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_audit_ledger_no_update ON audit_ledger_entries")
        op.execute("DROP TRIGGER IF EXISTS trg_audit_ledger_no_delete ON audit_ledger_entries")
        op.execute("DROP FUNCTION IF EXISTS prevent_audit_ledger_mutation()")

    op.drop_index("ix_audit_ledger_entries_entity_id", table_name="audit_ledger_entries")
    op.drop_index("ix_audit_ledger_entries_entity_type", table_name="audit_ledger_entries")
    op.drop_index("ix_audit_ledger_entries_action", table_name="audit_ledger_entries")
    op.drop_index("ix_audit_ledger_entries_id", table_name="audit_ledger_entries")
    op.drop_table("audit_ledger_entries")
