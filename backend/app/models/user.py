from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.template import EstimateTemplate
from app.models.estimate import Estimate



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    
    estimates = relationship(Estimate, back_populates="user", cascade="all, delete-orphan")
    templates = relationship(EstimateTemplate, back_populates="user", cascade="all, delete-orphan")