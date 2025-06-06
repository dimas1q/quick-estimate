from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.core.database import Base


class ClientLog(Base):
    __tablename__ = "client_logs"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
