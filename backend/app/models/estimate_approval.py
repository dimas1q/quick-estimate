from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class EstimateApprovalWorkflow(Base):
    __tablename__ = "estimate_approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(
        Integer,
        ForeignKey("estimates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    owner_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(32), nullable=False, default="draft", index=True)
    current_step_order = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    estimate = relationship("Estimate", back_populates="approval_workflow")
    owner = relationship(
        "User",
        foreign_keys=[owner_user_id],
        back_populates="approval_workflows_owned",
    )
    steps = relationship(
        "EstimateApprovalStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="EstimateApprovalStep.step_order.asc()",
    )


class EstimateApprovalStep(Base):
    __tablename__ = "estimate_approval_steps"
    __table_args__ = (
        UniqueConstraint("workflow_id", "step_order", name="uq_approval_step_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(
        Integer,
        ForeignKey("estimate_approval_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order = Column(Integer, nullable=False)
    stage_key = Column(String(40), nullable=False)
    stage_label = Column(String(80), nullable=False)

    approver_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(32), nullable=False, default="pending", index=True)

    signed_at = Column(DateTime(timezone=True), nullable=True)
    signature_name = Column(String(120), nullable=True)
    signature_hash = Column(String(64), nullable=True)
    decision = Column(String(16), nullable=True)
    decision_comment = Column(Text, nullable=True)
    decided_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    workflow = relationship("EstimateApprovalWorkflow", back_populates="steps")
    approver = relationship(
        "User",
        foreign_keys=[approver_user_id],
        back_populates="approval_steps_assigned",
    )
    decided_by = relationship(
        "User",
        foreign_keys=[decided_by_user_id],
        back_populates="approval_steps_decided",
    )
