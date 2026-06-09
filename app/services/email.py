import asyncio
import logging

import resend

from app.config import settings

logger = logging.getLogger(__name__)


async def send_verification_code(to_email: str, code: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set - skipping email send, code: %s", code)
        return True

    resend.api_key = settings.RESEND_API_KEY

    def _send():
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": "Ваш код подтверждения Weekly",
            "html": (
                f"<p>Ваш код подтверждения: <strong>{code}</strong></p>"
                f"<p>Код действителен 5 минут.</p>"
            ),
        })

    try:
        await asyncio.to_thread(_send)
        return True
    except Exception as e:
        logger.error("Failed to send verification email to %s: %s", to_email, e)
        return False