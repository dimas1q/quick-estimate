from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from app.core.database import Base


class EstimateChangeLog(Base):
    __tablename__ = "estimate_change_logs"

    id = Column(Integer, primary_key=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"))
    action = Column(String) 
    description = Column(Text)
    timestamp = Column(DateTime, default=func.now(), onupdate=func.now())
