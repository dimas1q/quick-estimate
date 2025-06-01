from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class EstimateFavorite(Base):
    __tablename__ = "estimate_favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'estimate_id', name='_user_estimate_uc'),)

    user = relationship("User", back_populates="favorites")
    estimate = relationship("Estimate", back_populates="favorites")