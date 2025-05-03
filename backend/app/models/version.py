# backend/app/models/version.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class EstimateVersion(Base):
    __tablename__ = "estimate_versions"

    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(
        Integer,
        ForeignKey("estimates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payload = Column(JSON, nullable=False)

    estimate = relationship("Estimate", back_populates="versions")
    user = relationship("User")
