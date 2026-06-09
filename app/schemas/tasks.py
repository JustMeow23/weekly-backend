import uuid
from datetime import time

from pydantic import BaseModel, field_serializer

class TaskSchema(BaseModel):
    id: uuid.UUID
    date: str
    title: str
    timeFrom: time
    timeTo: time
    isCompleted: bool
    isFavorite: bool
    type: str = "task"
    postponedCount: int = 0

    class Config:
        from_attributes = True

    @field_serializer('timeFrom', 'timeTo')
    def serialize_time(self, value: time) -> str:
        return value.strftime('%H:%M')

class CreateTaskRequest(BaseModel):
    date: str
    title: str
    timeFrom: time
    timeTo: time
    type: str = "task"

    class Config:
        from_attributes = True

class UpdateTaskRequest(BaseModel):
    title: str | None = None
    timeFrom: time | None = None
    timeTo: time | None = None
    isCompleted: bool | None = None
    isFavorite: bool | None = None
    type: str | None = None

class PostponeTaskRequest(BaseModel):
    date: str
    timeFrom: time
    timeTo: time

class StatsResponse(BaseModel):
    year: int
    completed: int
    missed: int
    postponed: int
    total: int
    percent: int