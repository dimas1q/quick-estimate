from email.message import EmailMessage
import aiosmtplib

from app.core.config import settings


async def send_verification_code(email: str, code: str) -> None:
    msg = EmailMessage()
    msg['From'] = settings.SMTP_SENDER
    msg['To'] = email
    msg['Subject'] = 'Код подтверждения'
    msg.set_content(f'Ваш код подтверждения: {code}')

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=settings.SMTP_TLS,
        use_tls=settings.SMTP_SSL,
    )
