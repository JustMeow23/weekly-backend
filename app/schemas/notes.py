import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class NoteSchema(BaseModel):
    id: uuid.UUID
    title: str | None = None
    content: str = ""
    createdAt: datetime = Field(validation_alias="created_at")
    updatedAt: datetime = Field(validation_alias="updated_at")

    class Config:
        from_attributes = True
        populate_by_name = True

    @field_serializer("createdAt", "updatedAt")
    def serialize_millis(self, value: datetime) -> int:
        return int(value.timestamp() * 1000)


class CreateNoteRequest(BaseModel):
    title: str | None = None
    content: str = ""

    class Config:
        from_attributes = True


class UpdateNoteRequest(BaseModel):
    title: str | None = None
    content: str | None = None