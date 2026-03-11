from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Адрес подключения к PostgreSQL в Docker
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db/quickestimate"

# Асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True)

# Сессия для запросов
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
