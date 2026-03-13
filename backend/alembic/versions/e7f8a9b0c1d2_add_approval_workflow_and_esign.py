"""add approval workflow and e-sign tables

Revision ID: e7f8a9b0c1d2
Revises: a7c1d9e2f4b6
Create Date: 2026-03-13 06:25:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "a7c1d9e2f4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "estimate_approval_workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "estimate_id",
            sa.Integer(),
            sa.ForeignKey("estimates.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "owner_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("current_step_order", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index(
        "ix_estimate_approval_workflows_estimate_id",
        "estimate_approval_workflows",
        ["estimate_id"],
    )
    op.create_index(
        "ix_estimate_approval_workflows_owner_user_id",
        "estimate_approval_workflows",
        ["owner_user_id"],
    )
    op.create_index(
        "ix_estimate_approval_workflows_status",
        "estimate_approval_workflows",
        ["status"],
    )

    op.create_table(
        "estimate_approval_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.Integer(),
            sa.ForeignKey("estimate_approval_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("stage_key", sa.String(length=40), nullable=False),
        sa.Column("stage_label", sa.String(length=80), nullable=False),
        sa.Column(
            "approver_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_name", sa.String(length=120), nullable=True),
        sa.Column("signature_hash", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=True),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column(
            "decided_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.UniqueConstraint("workflow_id", "step_order", name="uq_approval_step_order"),
    )
    op.create_index("ix_estimate_approval_steps_workflow_id", "estimate_approval_steps", ["workflow_id"])
    op.create_index(
        "ix_estimate_approval_steps_approver_user_id",
        "estimate_approval_steps",
        ["approver_user_id"],
    )
    op.create_index("ix_estimate_approval_steps_status", "estimate_approval_steps", ["status"])


def downgrade() -> None:
    op.drop_index("ix_estimate_approval_steps_status", table_name="estimate_approval_steps")
    op.drop_index("ix_estimate_approval_steps_approver_user_id", table_name="estimate_approval_steps")
    op.drop_index("ix_estimate_approval_steps_workflow_id", table_name="estimate_approval_steps")
    op.drop_table("estimate_approval_steps")

    op.drop_index("ix_estimate_approval_workflows_status", table_name="estimate_approval_workflows")
    op.drop_index("ix_estimate_approval_workflows_owner_user_id", table_name="estimate_approval_workflows")
    op.drop_index("ix_estimate_approval_workflows_estimate_id", table_name="estimate_approval_workflows")
    op.drop_table("estimate_approval_workflows")
