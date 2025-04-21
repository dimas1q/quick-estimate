from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    quantity = Column(Float, default=1)
    unit = Column(String, default="шт")
    unit_price = Column(Float, default=0)
    category = Column(String)

    estimate_id = Column(Integer, ForeignKey("estimates.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("estimate_templates.id"), nullable=True)

    estimate = relationship("Estimate", back_populates="items")
    template = relationship("EstimateTemplate", back_populates="items")