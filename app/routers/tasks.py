from datetime import date as date_type
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import uuid
import logging

from app.database import get_session
from app.schemas import (
    TaskSchema, CreateTaskRequest, UpdateTaskRequest,
    PostponeTaskRequest, StatsResponse, ErrorCode,
)
from app.dao.tasks import TaskDAO
from app.utils.auth_utils import get_current_user
from app.models import User
from app.exceptions import AppException

router = APIRouter(tags=["Tasks"])
logger = logging.getLogger(__name__)

@router.post("/tasks", response_model=List[TaskSchema])
async def add_task(
    task: CreateTaskRequest, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task_data = TaskSchema(
        id=uuid.uuid4(),
        date=task.date,
        title=task.title,
        timeFrom=task.timeFrom,
        timeTo=task.timeTo,
        isCompleted=False,
        isFavorite=False,
        type=task.type
    )

    await TaskDAO.add(session, task_data, current_user.id)
    return await TaskDAO.find_all_by_user_and_date(session, current_user.id, task.date)

@router.get("/tasks", response_model=List[TaskSchema])
async def get_tasks(
    date: str, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    tasks = await TaskDAO.find_all_by_user_and_date(session, current_user.id, date)
    return tasks

@router.patch("/tasks/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: UUID,
    task_update: UpdateTaskRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    updated_task = await TaskDAO.update(session, task_id, current_user.id, task_update.model_dump(exclude_unset=True))
    if updated_task is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, 
            error_code=ErrorCode.NOT_FOUND,
            detail="Task not found or access denied"
        )
    return updated_task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    success = await TaskDAO.delete(session, task_id, current_user.id)
    if not success:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            detail="Task not found or access denied"
        )

@router.post("/tasks/{task_id}/postpone", response_model=TaskSchema)
async def postpone_task(
    task_id: UUID,
    payload: PostponeTaskRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task = await TaskDAO.postpone(
        session, task_id, current_user.id,
        payload.date, payload.timeFrom, payload.timeTo
    )
    if task is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            detail="Task not found or access denied"
        )
    return task

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    year: int | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resolved_year = year if year is not None else date_type.today().year
    stats = await TaskDAO.compute_stats(session, current_user.id, resolved_year)
    return stats
