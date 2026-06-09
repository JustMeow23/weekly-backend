import logging

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _init_firebase() -> bool:
    """Инициализирует firebase-admin один раз. Возвращает True если успешно."""
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials
        from app.config import settings

        if firebase_admin._apps:
            _firebase_initialized = True
            return True

        if not settings.FIREBASE_CREDENTIALS_PATH:
            logger.warning("FIREBASE_CREDENTIALS_PATH not set - FCM disabled")
            return False

        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True

    except Exception as e:
        logger.error("Failed to initialize Firebase: %s", e)
        return False


async def send_multicast(tokens: list[str], title: str, body: str) -> int:
    """
    Отправляет data-only push на список FCM-токенов.
    Возвращает количество успешно доставленных.
    Если firebase не настроен - молча возвращает 0.
    """
    if not tokens:
        return 0
    if not _init_firebase():
        return 0

    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            tokens=tokens,
            data={"title": title, "body": body, "type": "news"},
        )
        response = messaging.send_each_for_multicast(message)
        logger.info("FCM multicast: %d success, %d failure",
                    response.success_count, response.failure_count)
        return response.success_count

    except Exception as e:
        logger.error("FCM send error: %s", e)
        return 0