# backend/app/models/estimate.py

from sqlalchemy import Column, Integer, String, DateTime, Text, func, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True, 
    )
    client = relationship(
        "Client",
        back_populates="estimates",
        passive_deletes=True, 
    )
    responsible = Column(String)
    notes = Column(Text, nullable=True)

    items = relationship("EstimateItem", back_populates="estimate", cascade="all, delete-orphan")

    from app.models.version import EstimateVersion

    versions = relationship(
        "EstimateVersion",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="EstimateVersion.version.desc()"
    )

    vat_enabled = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="estimates")
