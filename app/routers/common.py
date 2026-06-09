from fastapi import APIRouter
from app.schemas import PingResponse
from app.schemas.common import AppStatusResponse
from app.config import settings

router = APIRouter(tags=["Common"])

@router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse(status="ok")

@router.get("/status", response_model=AppStatusResponse)
async def app_status() -> AppStatusResponse:
    return AppStatusResponse(
        captcha=settings.CAPTCHA_ENABLED,
        emailCode=settings.EMAIL_CODE_ENABLED,
    )
