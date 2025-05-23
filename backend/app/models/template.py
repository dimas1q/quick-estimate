from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class EstimateTemplate(Base):
    __tablename__ = "estimate_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    items = relationship(
        "EstimateItem", back_populates="template", cascade="all, delete-orphan"
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="templates")
