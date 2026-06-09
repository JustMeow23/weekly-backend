from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailVerificationCode


class EmailVerificationCodeDAO:

    @classmethod
    async def find_by_email(cls, session: AsyncSession, email: str) -> EmailVerificationCode | None:
        result = await session.execute(
            select(EmailVerificationCode).where(EmailVerificationCode.email == email)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def delete_by_email(cls, session: AsyncSession, email: str) -> None:
        await session.execute(
            delete(EmailVerificationCode).where(EmailVerificationCode.email == email)
        )

    @classmethod
    async def create(cls, session: AsyncSession, email: str, code: str, expires_at: datetime) -> EmailVerificationCode:
        obj = EmailVerificationCode(email=email, code=code, expires_at=expires_at)
        session.add(obj)
        await session.flush()
        return obj