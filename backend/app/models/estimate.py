from sqlalchemy import Column, Integer, String, DateTime, Text, func, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    client_name = Column(String)
    client_company = Column(String)
    client_contact = Column(String)
    responsible = Column(String)
    notes = Column(Text, nullable=True)
    items = relationship("EstimateItem", back_populates="estimate", cascade="all, delete-orphan")
    vat_enabled = Column(Boolean, default=True)
