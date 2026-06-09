from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from uuid import UUID
from app.schemas.tasks import TaskSchema
from datetime import datetime
from .enums import UserRole


class User(BaseModel):
    id: UUID
    fullName: str = Field(min_length=2, max_length=50)
    email: EmailStr = Field(max_length=254)
    # is_active: bool # Повторка видимо
    role: UserRole
    isActive: bool = Field(validation_alias="is_active")
    avatarUrl: str = Field(default="https://s3.komaru-best.cfd/weekly/avatars/default.png", validation_alias="avatar_url")
    createdAt: datetime = Field(default_factory=datetime.now, validation_alias="created_at")
    updatedAt: datetime = Field(default_factory=datetime.now, validation_alias="updated_at")
    referralCode: Optional[str] = None
    tasks: List[TaskSchema] = []

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    fullName: str = Field(min_length=2, max_length=50)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = Field(None, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class FcmTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)


class PagedUsers(BaseModel):
    items: list[User]
    total: int = Field(ge=0)
    page: int = Field(ge=0)
    size: int = Field(ge=1)
