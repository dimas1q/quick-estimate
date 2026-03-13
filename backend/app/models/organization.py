from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

WORKSPACE_ROLE_OWNER = "owner"
WORKSPACE_ROLE_ADMIN = "admin"
WORKSPACE_ROLE_APPROVER = "approver"
WORKSPACE_ROLE_ESTIMATOR = "estimator"
WORKSPACE_ROLE_GUEST = "guest"

WORKSPACE_ROLES = {
    WORKSPACE_ROLE_OWNER,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_APPROVER,
    WORKSPACE_ROLE_ESTIMATOR,
    WORKSPACE_ROLE_GUEST,
}

WORKSPACE_INVITE_STATUS_PENDING = "pending"
WORKSPACE_INVITE_STATUS_ACCEPTED = "accepted"
WORKSPACE_INVITE_STATUS_REVOKED = "revoked"
WORKSPACE_INVITE_STATUS_EXPIRED = "expired"

WORKSPACE_INVITE_STATUSES = {
    WORKSPACE_INVITE_STATUS_PENDING,
    WORKSPACE_INVITE_STATUS_ACCEPTED,
    WORKSPACE_INVITE_STATUS_REVOKED,
    WORKSPACE_INVITE_STATUS_EXPIRED,
}


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    domain = Column(String(120), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    members = relationship(
        "OrganizationMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    users = relationship(
        "User",
        secondary="organization_memberships",
        viewonly=True,
    )


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_membership",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(32), nullable=False, default=WORKSPACE_ROLE_ESTIMATOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")


class WorkspaceInvitation(Base):
    __tablename__ = "workspace_invitations"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_workspace_invitations_token_hash"),
        Index(
            "ix_workspace_invitations_pending_email",
            "organization_id",
            "email",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(32), nullable=False, default=WORKSPACE_ROLE_ESTIMATOR)
    token_hash = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default=WORKSPACE_INVITE_STATUS_PENDING)
    invited_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization = relationship("Organization")
    invited_by_user = relationship(
        "User",
        foreign_keys=[invited_by_user_id],
        back_populates="workspace_invitations_sent",
        overlaps="workspace_invitations_sent",
    )
    accepted_by_user = relationship(
        "User",
        foreign_keys=[accepted_by_user_id],
        back_populates="workspace_invitations_accepted",
        overlaps="workspace_invitations_accepted",
    )
