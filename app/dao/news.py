from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models import Changelog


class NewsDAO:
    @classmethod
    async def get_all(cls, session: AsyncSession) -> List[Changelog]:
        query = select(Changelog).order_by(Changelog.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_latest(cls, session: AsyncSession) -> Optional[Changelog]:
        query = select(Changelog).order_by(Changelog.created_at.desc()).limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        query = select(func.count()).select_from(Changelog)
        result = await session.execute(query)
        return result.scalar()

    @classmethod
    async def create(cls, session: AsyncSession, version: str, items: List[str]) -> Changelog:
        entry = Changelog(version=version, items=items)
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry

    @classmethod
    async def delete(cls, session: AsyncSession, changelog_id: int) -> bool:
        query = select(Changelog).where(Changelog.id == changelog_id)
        result = await session.execute(query)
        entry = result.scalar_one_or_none()
        if entry is None:
            return False
        await session.delete(entry)
        await session.commit()
        return True

    @classmethod
    async def seed(cls, session: AsyncSession, changelogs: List[dict]) -> None:
        count = await cls.count(session)
        if count == 0:
            for data in changelogs:
                session.add(Changelog(**data))
            await session.commit()