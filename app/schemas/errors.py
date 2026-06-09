from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel
from .enums import ErrorCode


class ApiError(BaseModel):
    code: ErrorCode
    message: str
    traceId: UUID
    timestamp: datetime
    path: str
    details: Optional[dict] = None


class FieldError(BaseModel):
    field: str
    issue: str
    rejectedValue: Optional[Any] = None


class ValidationError(BaseModel):
    code: str = "VALIDATION_FAILED"
    message: str
    traceId: UUID
    timestamp: datetime
    path: str
    fieldErrors: list[FieldError]
