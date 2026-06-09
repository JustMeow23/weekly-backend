from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List
from app.models import User


class UserDAO:
    @classmethod
    async def find_all(cls, session: AsyncSession):
        query = select(User).options(selectinload(User.tasks))
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_by_email(cls, session: AsyncSession, email: str):
        query = select(User).options(selectinload(User.tasks)).where(User.email == email)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def find_by_id(cls, session: AsyncSession, user_id: UUID):
        query = select(User).options(selectinload(User.tasks)).where(User.id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def find_by_id_with_tasks(cls, session: AsyncSession, user_id: UUID):
        return await cls.find_by_id(session, user_id)

    @classmethod
    async def find_all_paged(cls, session: AsyncSession, page: int, size: int):
        offset = page * size

        query = select(User).options(selectinload(User.tasks)).limit(size).offset(offset)
        result = await session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(User.id)).select_from(User)
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        return items, total

    @classmethod
    async def add(cls, session: AsyncSession, user_data: dict):
        new_user = User(**user_data)
        session.add(new_user)
        await session.commit()
        
        # Reload with tasks
        return await cls.find_by_id(session, new_user.id)

    @classmethod
    async def add_and_load_tasks(cls, session: AsyncSession, user_data: dict):
        return await cls.add(session, user_data)

    @classmethod
    async def update(cls, session: AsyncSession, user: User, update_data: dict):
        for key, value in update_data.items():
            setattr(user, key, value)
        await session.commit()

        return await cls.find_by_id(session, user.id)

    @classmethod
    async def find_all_fcm_tokens(cls, session: AsyncSession) -> List[str]:
        query = select(User.fcm_token).where(
            User.fcm_token.isnot(None),
            User.is_active == True,
        )
        result = await session.execute(query)
        return [row[0] for row in result.fetchall()]
