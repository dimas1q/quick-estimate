from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    description = Column(String)
    quantity = Column(Float, default=1)
    unit = Column(String, default="шт")
    unit_price = Column(Float, default=0)
    category = Column(String)

    estimate = relationship("Estimate", back_populates="items")
