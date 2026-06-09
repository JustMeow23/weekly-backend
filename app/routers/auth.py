import secrets
from datetime import timezone, timedelta, datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.config import settings
from app.models import RefreshToken, User
from app.schemas import PingResponse, AuthResponse, RegisterRequest, LoginRequest, User as UserSchema, ErrorCode, UserRole, RefreshTokenRequest, SendCodeRequest, SendCodeResponse, ChangePasswordRequest
from app.database import get_session
from app.dao.user import UserDAO
from app.dao.email_verification import EmailVerificationCodeDAO
from app.utils.auth_utils import get_password_hash, create_access_token, verify_password, create_refresh_token, get_current_user
from app.utils.captcha import verify_captcha
from app.exceptions import AppException
from app.services.email import send_verification_code

router = APIRouter(tags=["Auth"])
logger = logging.getLogger(__name__)


@router.post("/auth/send-code", response_model=SendCodeResponse, status_code=status.HTTP_200_OK)
async def send_code(body: SendCodeRequest, raw_request: Request, session: AsyncSession = Depends(get_session)) -> SendCodeResponse:
    if not settings.EMAIL_CODE_ENABLED:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            detail="Email verification is not enabled",
        )

    captcha_ok = await verify_captcha(body.captchaToken, raw_request.client.host)
    if not captcha_ok:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.CAPTCHA_FAILED,
            detail="Captcha verification failed",
        )

    existing_user = await UserDAO.find_by_email(session, body.email)
    if existing_user:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            detail="Пользователь с таким email уже существует",
            extra_details={"field": "email", "value": body.email},
        )

    existing_code = await EmailVerificationCodeDAO.find_by_email(session, body.email)
    if existing_code:
        now = datetime.now(timezone.utc)
        age_seconds = (now - existing_code.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        if age_seconds < 60:
            retry_after = int(60 - age_seconds)
            raise AppException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                detail="Слишком много запросов. Попробуйте позже.",
                extra_details={"retryAfterSeconds": retry_after},
            )
        await EmailVerificationCodeDAO.delete_by_email(session, body.email)

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    await EmailVerificationCodeDAO.create(session, body.email, code, expires_at)
    await session.commit()

    await send_verification_code(body.email, code)

    return SendCodeResponse(message="Код отправлен на указанный адрес")


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, raw_request: Request, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    if not settings.EMAIL_CODE_ENABLED:
        captcha_ok = await verify_captcha(body.captchaToken, raw_request.client.host)
        if not captcha_ok:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.CAPTCHA_FAILED,
                detail="Captcha verification failed",
            )

    existing_user = await UserDAO.find_by_email(session, body.email)
    if existing_user:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            detail="Пользователь с таким email уже существует",
            extra_details={"field": "email", "value": body.email}
        )

    if settings.EMAIL_CODE_ENABLED:
        if not body.verificationCode:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.VERIFICATION_CODE_NOT_FOUND,
                detail="Код подтверждения обязателен",
            )
        stored = await EmailVerificationCodeDAO.find_by_email(session, body.email)
        if not stored:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.VERIFICATION_CODE_NOT_FOUND,
                detail="Код не найден. Запросите новый.",
            )
        if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) or stored.code != body.verificationCode:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.VERIFICATION_CODE_INVALID,
                detail="Неверный или просроченный код подтверждения",
            )
        await EmailVerificationCodeDAO.delete_by_email(session, body.email)

    user_data = body.model_dump()
    user_data.pop("captchaToken", None)
    user_data.pop("verificationCode", None)
    user_data["password"] = get_password_hash(user_data["password"])
    user_data["role"] = UserRole.USER
    user_data["is_active"] = True

    new_user = await UserDAO.add(session, user_data)
    access_token = create_access_token(data={"sub": str(new_user.id),
                                             "role": new_user.role.value})

    refresh_token_str = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=new_user.id,
        expires_at=expires_at)
    session.add(new_refresh_token)
    await session.commit()

    return AuthResponse(
        accessToken=access_token,
        refreshToken=refresh_token_str,
        expiresIn=3600,
        user=UserSchema.model_validate(new_user, from_attributes=True)
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    user = await UserDAO.find_by_email(session, request.email)
    if not user or not verify_password(request.password, user.password):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            detail="Неверный email или пароль"
        )

    if not user.is_active:
        raise AppException(
            status_code=status.HTTP_423_LOCKED,
            error_code=ErrorCode.USER_INACTIVE,
            detail="Пользователь деактивирован"
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    refresh_token_str = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=expires_at
    )
    session.add(new_refresh_token)
    await session.commit()

    return AuthResponse(
        accessToken=access_token,
        refreshToken=refresh_token_str,
        expiresIn=3600,
        user=UserSchema.model_validate(user, from_attributes=True)
    )


@router.post("/auth/refresh", response_model=AuthResponse)
async def refresh_tokens(request: RefreshTokenRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    query = select(RefreshToken).where(RefreshToken.token == request.refreshToken)
    result = await session.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            detail="Токен не найден"
        )

    if db_token.expires_at < datetime.now(timezone.utc):
        await session.delete(db_token)
        await session.commit()
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            detail="Токен истёк"
        )

    user = await UserDAO.find_by_id(session, db_token.user_id)
    if not user:
         raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            detail="Пользователь не найден"
        )

    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    return AuthResponse(
        accessToken=new_access_token,
        refreshToken=db_token.token,
        expiresIn=3600,
        user=UserSchema.model_validate(user, from_attributes=True)
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: RefreshTokenRequest, session: AsyncSession = Depends(get_session)):
    query = delete(RefreshToken).where(RefreshToken.token == request.refreshToken)
    await session.execute(query)
    await session.commit()


@router.post("/auth/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
        body: ChangePasswordRequest,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    if not verify_password(body.oldPassword, current_user.password):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.BAD_REQUEST,
            detail="Текущий пароль неверен"
        )
    await UserDAO.update(session, current_user, {"password": get_password_hash(body.newPassword)})