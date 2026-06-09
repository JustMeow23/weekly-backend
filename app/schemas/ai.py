from pydantic import BaseModel
from typing import List


class SplitTaskRequest(BaseModel):
    title: str
    timeFrom: str
    timeTo: str
    date: str


class SubtaskSuggestion(BaseModel):
    title: str
    timeFrom: str
    timeTo: str


class SplitTaskResponse(BaseModel):
    subtasks: List[SubtaskSuggestion]
    usedThisWeek: int
    weeklyLimit: int