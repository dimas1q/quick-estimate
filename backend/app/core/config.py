from pydantic import BaseSettings, EmailStr


class Settings(BaseSettings):
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: EmailStr = "noreply@example.com"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    OTP_EXPIRE_MINUTES: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
