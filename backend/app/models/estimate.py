# backend/app/models/estimate.py

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class EstimateStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    event_datetime = Column(DateTime(timezone=True), nullable=True)
    event_place = Column(String, nullable=True)

    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=True,
    )
    client = relationship(
        "Client",
        back_populates="estimates",
        passive_deletes=True,
    )
    responsible = Column(String, nullable=False)
    notes = relationship(
        "Note", back_populates="estimate", cascade="all, delete-orphan"
    )

    items = relationship(
        "EstimateItem", back_populates="estimate", cascade="all, delete-orphan"
    )

    status = Column(
        SQLEnum(EstimateStatus, name="estimate_status"),
        nullable=False,
        default=EstimateStatus.DRAFT,
    )

    from app.models.estimate_favorite import EstimateFavorite

    favorites = relationship(
        "EstimateFavorite", back_populates="estimate", cascade="all, delete-orphan"
    )

    from app.models.version import EstimateVersion

    versions = relationship(
        "EstimateVersion",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="EstimateVersion.version.desc()",
    )

    vat_enabled = Column(Boolean, default=True)
    vat_rate = Column(Integer, default=20, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="estimates")
