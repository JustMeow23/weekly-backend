from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime


class NewsPushRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=1000)


class NewsPushResponse(BaseModel):
    sent: int
    total_tokens: int


class ChangelogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    version: str
    items: List[str]
    createdAt: datetime = Field(validation_alias="created_at")


class ChangelogCreateRequest(BaseModel):
    version: str = Field(min_length=1)
    items: List[str] = Field(min_length=1)