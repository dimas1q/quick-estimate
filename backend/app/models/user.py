from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.template import EstimateTemplate
from app.models.estimate import Estimate
from app.models.client import Client



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    from app.models.estimate_favorite import EstimateFavorite

    favorites = relationship(
        "EstimateFavorite",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    estimates = relationship(
        Estimate, back_populates="user", cascade="all, delete-orphan"
    )
    templates = relationship(
        EstimateTemplate, back_populates="user", cascade="all, delete-orphan"
    )
    clients = relationship(Client, back_populates="user", cascade="all, delete-orphan")
