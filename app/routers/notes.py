import uuid
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import (
    NoteSchema, CreateNoteRequest, UpdateNoteRequest, ErrorCode,
)
from app.dao.notes import NoteDAO
from app.utils.auth_utils import get_current_user
from app.models import User
from app.exceptions import AppException

router = APIRouter(tags=["Notes"])
logger = logging.getLogger(__name__)


@router.post("/notes", response_model=NoteSchema)
async def add_note(
    note: CreateNoteRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    note_data = NoteSchema.model_construct(
        id=uuid.uuid4(),
        title=note.title,
        content=note.content,
    )
    return await NoteDAO.add(session, note_data, current_user.id)


@router.get("/notes", response_model=List[NoteSchema])
async def get_notes(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await NoteDAO.find_all_by_user(session, current_user.id)


@router.patch("/notes/{note_id}", response_model=NoteSchema)
async def update_note(
    note_id: UUID,
    note_update: UpdateNoteRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    updated_note = await NoteDAO.update(
        session, note_id, current_user.id, note_update.model_dump(exclude_unset=True)
    )
    if updated_note is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            detail="Note not found or access denied",
        )
    return updated_note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    success = await NoteDAO.delete(session, note_id, current_user.id)
    if not success:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            detail="Note not found or access denied",
        )