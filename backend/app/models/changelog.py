from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text,
                        func, JSON)
from sqlalchemy.orm import relationship

from app.core.database import Base


class EstimateChangeLog(Base):
    __tablename__ = "estimate_change_logs"

    id = Column(Integer, primary_key=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String)
    description = Column(Text)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User")
