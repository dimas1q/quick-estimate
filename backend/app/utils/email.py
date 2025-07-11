import aiosmtplib
from email.message import EmailMessage
from app.core.config import settings


async def send_email(subject: str, body: str, to: str):
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=settings.SMTP_TLS,
        use_tls=settings.SMTP_SSL,
    )


async def send_verification_code(email: str, code: str):
    subject = "Подтверждение регистрации"
    body = f"Ваш код подтверждения: {code}"
    await send_email(subject, body, email)
