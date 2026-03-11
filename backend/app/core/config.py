from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db/quickestimate"
    SQLALCHEMY_ECHO: bool = True

    JWT_SECRET_KEY: str | None = None
    JWT_SECRET_KEY_PATH: str = "config/secret.key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: EmailStr = "noreply@example.com"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    OTP_EXPIRE_MINUTES: int = 10


settings = Settings()
