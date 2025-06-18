from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True)
    template_id = Column(Integer, ForeignKey("estimate_templates.id", ondelete="CASCADE"), nullable=True)

    user = relationship("User", back_populates="notes")
    estimate = relationship("Estimate", back_populates="notes")
    client = relationship("Client", back_populates="notes")
    template = relationship("EstimateTemplate", back_populates="notes")
