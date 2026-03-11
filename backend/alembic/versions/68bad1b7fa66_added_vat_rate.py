"""Added vat_rate

Revision ID: 68bad1b7fa66
Revises: 
Create Date: 2025-05-28 11:45:16.975807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68bad1b7fa66'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("login", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("company", sa.String(), nullable=True),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )

    if "clients" not in tables:
        op.create_table(
            "clients",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("company", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("address", sa.String(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        )

    if "estimate_templates" not in tables:
        op.create_table(
            "estimate_templates",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        )

    if "estimates" not in tables:
        op.create_table(
            "estimates",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("date", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("responsible", sa.String(), nullable=True),
            sa.Column(
                "status",
                sa.Enum("draft", "sent", "approved", "paid", "cancelled", name="estimate_status"),
                nullable=False,
                server_default="draft",
            ),
            sa.Column("vat_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        )

    if "estimate_items" not in tables:
        op.create_table(
            "estimate_items",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("quantity", sa.Float(), nullable=True, server_default="1"),
            sa.Column("unit", sa.String(), nullable=True, server_default="шт"),
            sa.Column("unit_price", sa.Float(), nullable=True),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id"), nullable=True),
            sa.Column("template_id", sa.Integer(), sa.ForeignKey("estimate_templates.id"), nullable=True),
        )

    if "estimate_change_logs" not in tables:
        op.create_table(
            "estimate_change_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="CASCADE")),
            sa.Column("action", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if "estimate_versions" not in tables:
        op.create_table(
            "estimate_versions",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
        )

    if "estimate_favorites" not in tables:
        op.create_table(
            "estimate_favorites",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False),
            sa.UniqueConstraint("user_id", "estimate_id", name="_user_estimate_uc"),
        )

    inspector = sa.inspect(conn)
    estimate_columns = {column["name"] for column in inspector.get_columns("estimates")}
    if "vat_rate" not in estimate_columns:
        op.add_column(
            "estimates",
            sa.Column("vat_rate", sa.Integer(), nullable=False, server_default="20"),
        )
        op.alter_column("estimates", "vat_rate", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    estimate_columns = {column["name"] for column in inspector.get_columns("estimates")}
    if "vat_rate" in estimate_columns:
        op.drop_column("estimates", "vat_rate")
