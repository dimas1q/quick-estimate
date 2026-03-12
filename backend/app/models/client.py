## backend/app/models/client.py

import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ClientPipelineStage(str, enum.Enum):
    LEAD = "lead"
    QUOTE = "quote"
    APPROVED = "approved"
    PAID = "paid"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    legal_address = Column(String, nullable=True)
    actual_address = Column(String, nullable=True)
    inn = Column(String, nullable=True)
    kpp = Column(String, nullable=True)
    bik = Column(String, nullable=True)
    account = Column(String, nullable=True)
    bank = Column(String, nullable=True)
    corr_account = Column(String, nullable=True)
    pipeline_stage = Column(
        SQLEnum(
            ClientPipelineStage,
            name="client_pipeline_stage",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ClientPipelineStage.LEAD,
    )
    pipeline_expected_revenue = Column(Float, nullable=False, default=0.0)
    notes = relationship(
        "Note", back_populates="client", cascade="all, delete-orphan"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="clients")

    estimates = relationship(
        "Estimate", back_populates="client", passive_deletes=True, cascade="save-update"
    )
