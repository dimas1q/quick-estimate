from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
