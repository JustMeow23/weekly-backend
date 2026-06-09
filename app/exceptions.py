from typing import Any, Optional
from fastapi import HTTPException
from app.schemas import ErrorCode


class AppException(HTTPException):
    def __init__(
            self,
            status_code: int,
            error_code: ErrorCode,
            detail: Any = None,
            headers: Optional[dict[str, Any]] = None,
            extra_details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.extra_details = extra_details
