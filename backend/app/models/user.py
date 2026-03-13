from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.template import EstimateTemplate
from app.models.estimate import Estimate
from app.models.client import Client



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default="0")
    failed_login_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)
    hashed_otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_sent_at = Column(DateTime(timezone=True), nullable=True)
    current_organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    default_organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    from app.models.estimate_favorite import EstimateFavorite

    favorites = relationship(
        "EstimateFavorite",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    estimates = relationship(
        Estimate, back_populates="user", cascade="all, delete-orphan"
    )
    templates = relationship(
        EstimateTemplate, back_populates="user", cascade="all, delete-orphan"
    )
    clients = relationship(Client, back_populates="user", cascade="all, delete-orphan")

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    current_organization = relationship("Organization", foreign_keys=[current_organization_id])
    default_organization = relationship("Organization", foreign_keys=[default_organization_id])
    organization_memberships = relationship(
        "OrganizationMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    approval_workflows_owned = relationship(
        "EstimateApprovalWorkflow",
        foreign_keys="EstimateApprovalWorkflow.owner_user_id",
        back_populates="owner",
    )
    approval_steps_assigned = relationship(
        "EstimateApprovalStep",
        foreign_keys="EstimateApprovalStep.approver_user_id",
        back_populates="approver",
    )
    approval_steps_decided = relationship(
        "EstimateApprovalStep",
        foreign_keys="EstimateApprovalStep.decided_by_user_id",
        back_populates="decided_by",
    )
    workspace_invitations_sent = relationship(
        "WorkspaceInvitation",
        foreign_keys="WorkspaceInvitation.invited_by_user_id",
        back_populates="invited_by_user",
        overlaps="invited_by_user",
    )
    workspace_invitations_accepted = relationship(
        "WorkspaceInvitation",
        foreign_keys="WorkspaceInvitation.accepted_by_user_id",
        back_populates="accepted_by_user",
        overlaps="accepted_by_user",
    )
