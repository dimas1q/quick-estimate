"""add client pipeline fields

Revision ID: f3b7c9d1e2f4
Revises: d1e2f3a4b5c6
Create Date: 2026-03-13 03:35:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3b7c9d1e2f4"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PIPELINE_STAGE_ENUM = sa.Enum(
    "lead",
    "quote",
    "approved",
    "paid",
    name="client_pipeline_stage",
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("clients")}

    PIPELINE_STAGE_ENUM.create(bind, checkfirst=True)

    if "pipeline_stage" not in columns:
        op.add_column(
            "clients",
            sa.Column(
                "pipeline_stage",
                PIPELINE_STAGE_ENUM,
                nullable=False,
                server_default="lead",
            ),
        )
        op.alter_column("clients", "pipeline_stage", server_default=None)

    if "pipeline_expected_revenue" not in columns:
        op.add_column(
            "clients",
            sa.Column(
                "pipeline_expected_revenue",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.alter_column("clients", "pipeline_expected_revenue", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("clients")}

    if "pipeline_expected_revenue" in columns:
        op.drop_column("clients", "pipeline_expected_revenue")
    if "pipeline_stage" in columns:
        op.drop_column("clients", "pipeline_stage")

    PIPELINE_STAGE_ENUM.drop(bind, checkfirst=True)
