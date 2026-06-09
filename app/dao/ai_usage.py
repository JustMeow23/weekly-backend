from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models import AiUsage


class AiUsageDAO:

    @classmethod
    async def get_or_create(
        cls, session: AsyncSession, user_id: UUID, feature_key: str, week_number: int, year: int
    ) -> AiUsage:
        query = select(AiUsage).where(
            AiUsage.user_id == user_id,
            AiUsage.feature_key == feature_key,
            AiUsage.week_number == week_number,
            AiUsage.year == year,
        )
        result = await session.execute(query)
        record = result.scalar_one_or_none()
        if record is None:
            record = AiUsage(
                user_id=user_id,
                feature_key=feature_key,
                week_number=week_number,
                year=year,
                count=0,
            )
            session.add(record)
            await session.flush()
        return record

    @classmethod
    async def increment(cls, session: AsyncSession, record: AiUsage) -> AiUsage:
        record.count += 1
        await session.commit()
        await session.refresh(record)
        return record