from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text,
                        func)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClientChangeLog(Base):
    __tablename__ = "client_change_logs"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String)
    description = Column(Text)
    timestamp = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User")
