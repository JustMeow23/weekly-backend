from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note
from app.schemas.notes import NoteSchema


class NoteDAO:
    @classmethod
    async def find_all_by_user(cls, session: AsyncSession, user_id: UUID) -> List[Note]:
        query = (
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.updated_at.desc())
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_by_id(cls, session: AsyncSession, note_id: UUID, user_id: UUID) -> Optional[Note]:
        query = select(Note).where(Note.id == note_id, Note.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def add(cls, session: AsyncSession, note_data: NoteSchema, user_id: UUID) -> Note:
        db_note = Note(
            id=note_data.id,
            title=note_data.title,
            content=note_data.content,
            user_id=user_id,
        )
        session.add(db_note)
        await session.commit()
        await session.refresh(db_note)
        return db_note

    @classmethod
    async def update(cls, session: AsyncSession, note_id: UUID, user_id: UUID, update_data: dict) -> Optional[Note]:
        query = select(Note).where(Note.id == note_id, Note.user_id == user_id)
        result = await session.execute(query)
        db_note = result.scalar_one_or_none()
        if db_note:
            for key, value in update_data.items():
                setattr(db_note, key, value)
            await session.commit()
            await session.refresh(db_note)
        return db_note

    @classmethod
    async def delete(cls, session: AsyncSession, note_id: UUID, user_id: UUID) -> bool:
        query = select(Note).where(Note.id == note_id, Note.user_id == user_id)
        result = await session.execute(query)
        db_note = result.scalar_one_or_none()
        if db_note:
            await session.delete(db_note)
            await session.commit()
            return True
        return False