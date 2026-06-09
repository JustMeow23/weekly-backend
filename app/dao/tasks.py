from datetime import date as date_type, time
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Task
from app.schemas.tasks import TaskSchema
from uuid import UUID
from typing import List

class TaskDAO:
    @classmethod
    async def find_all_by_user_and_date(cls, session: AsyncSession, user_id: UUID, date: str) -> List[Task]:
        query = select(Task).where(Task.user_id == user_id, Task.date == date).order_by(
            Task.isFavorite.desc(), 
            Task.isCompleted.asc(),
            Task.created_at.asc()
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def add(cls, session: AsyncSession, task_data: TaskSchema, user_id: UUID) -> Task:
        db_task = Task(
            id=task_data.id,
            date=task_data.date,
            title=task_data.title,
            timeFrom=task_data.timeFrom,
            timeTo=task_data.timeTo,
            isCompleted=task_data.isCompleted,
            isFavorite=task_data.isFavorite,
            type=task_data.type,
            user_id=user_id
        )
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)
        return db_task

    @classmethod
    async def update(cls, session: AsyncSession, task_id: UUID, user_id: UUID, update_data: dict) -> Task:
        query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await session.execute(query)
        db_task = result.scalar_one_or_none()
        if db_task:
            for key, value in update_data.items():
                setattr(db_task, key, value)
            await session.commit()
            await session.refresh(db_task)
        return db_task

    @classmethod
    async def delete(cls, session: AsyncSession, task_id: UUID, user_id: UUID) -> bool:
        query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await session.execute(query)
        db_task = result.scalar_one_or_none()
        if db_task:
            await session.delete(db_task)
            await session.commit()
            return True
        return False

    @classmethod
    async def postpone(cls, session: AsyncSession, task_id: UUID, user_id: UUID,
                       new_date: str, time_from: time, time_to: time) -> Task:
        query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await session.execute(query)
        db_task = result.scalar_one_or_none()
        if db_task:
            db_task.postponedCount = (db_task.postponedCount or 0) + 1
            db_task.date = new_date
            db_task.timeFrom = time_from
            db_task.timeTo = time_to
            await session.commit()
            await session.refresh(db_task)
        return db_task

    @classmethod
    async def compute_stats(cls, session: AsyncSession, user_id: UUID, year: int) -> dict:
        today = date_type.today().isoformat()
        completed_c = func.count(case((Task.isCompleted.is_(True), 1)))
        missed_c = func.count(
            case((and_(Task.isCompleted.is_(False), Task.date < today), 1))
        )
        postponed_c = func.count(
            case((and_(Task.isCompleted.is_(False),
                       Task.date >= today,
                       Task.postponedCount > 0), 1))
        )

        query = select(
            completed_c.label("completed"),
            missed_c.label("missed"),
            postponed_c.label("postponed"),
        ).where(
            Task.user_id == user_id,
            Task.type == "task",
            Task.date.like(f"{year}-%"),
        )
        row = (await session.execute(query)).one()
        completed, missed, postponed = row.completed, row.missed, row.postponed

        total = completed + missed + postponed
        percent = round(completed / total * 100) if total > 0 else 0
        return {
            "year": year,
            "completed": completed,
            "missed": missed,
            "postponed": postponed,
            "total": total,
            "percent": percent,
        }
