import httpx
from app.config import settings

YANDEX_CAPTCHA_URL = "https://smartcaptcha.yandexcloud.net/validate"


async def verify_captcha(token: str | None, ip: str) -> bool:
    if not settings.YANDEX_CAPTCHA_SECRET_KEY:
        return True
    if not token:
        return False
    async with httpx.AsyncClient() as client:
        resp = await client.post(YANDEX_CAPTCHA_URL, data={
            "secret": settings.YANDEX_CAPTCHA_SECRET_KEY,
            "token": token,
            "ip": ip,
        })
        data = resp.json()
        return data.get("status") == "ok"