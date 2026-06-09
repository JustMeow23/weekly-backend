from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models import AiFeatureConfig


class AiConfigDAO:

    @classmethod
    async def get_limit(cls, session: AsyncSession, feature_key: str) -> int:
        query = select(AiFeatureConfig).where(AiFeatureConfig.feature_key == feature_key)
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        return config.free_weekly_limit if config else 3

    @classmethod
    async def seed(cls, session: AsyncSession, configs: List[dict]) -> None:
        for cfg in configs:
            query = select(AiFeatureConfig).where(
                AiFeatureConfig.feature_key == cfg["feature_key"]
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if existing is None:
                session.add(AiFeatureConfig(**cfg))
        await session.commit()