from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class EstimateTemplate(Base):
    __tablename__ = "estimate_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    notes = relationship(
        "Note", back_populates="template", cascade="all, delete-orphan"
    )

    items = relationship(
        "EstimateItem", back_populates="template", cascade="all, delete-orphan"
    )

    use_internal_price = Column(Boolean, default=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="templates")
