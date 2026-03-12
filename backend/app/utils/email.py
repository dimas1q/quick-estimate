import logging

import aiosmtplib
from email.message import EmailMessage
from typing import Iterable, TypedDict

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailAttachment(TypedDict):
    filename: str
    content: bytes
    content_type: str


async def send_email(
    subject: str,
    body: str,
    to: str,
    attachments: Iterable[EmailAttachment] | None = None,
):
    if settings.SMTP_TLS and settings.SMTP_SSL:
        raise RuntimeError("SMTP_TLS и SMTP_SSL не могут быть включены одновременно")

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body or "")

    for attachment in attachments or []:
        content_type = attachment.get("content_type", "application/octet-stream")
        if "/" not in content_type:
            content_type = "application/octet-stream"
        maintype, subtype = content_type.split("/", 1)
        message.add_attachment(
            attachment["content"],
            maintype=maintype,
            subtype=subtype,
            filename=attachment["filename"],
        )

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
            use_tls=settings.SMTP_SSL,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.exception("SMTP send failed")
        raise RuntimeError("Не удалось отправить email") from exc


async def send_verification_code(email: str, code: str):
    subject = "Подтверждение аккаунта"
    body = f"Ваш код подтверждения: {code}"
    await send_email(subject, body, email)
