from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Асинхронный движок SQLAlchemy
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Сессия для запросов
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
