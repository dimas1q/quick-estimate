import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() == "true"
    SMTP_SSL = os.getenv("SMTP_SSL", "false").lower() == "true"
    SMTP_SENDER = os.getenv("SMTP_SENDER", "no-reply@example.com")

settings = Settings()
