from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    status_code: int


def create_success_response(
    message: str = "Success", data: Any = None, status_code: int = 200
) -> ApiResponse:
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        status_code=status_code,
    )


def create_error_response(
    message: str = "Error", data: Any = None, status_code: int = 400
) -> ApiResponse:
    return ApiResponse(
        success=False,
        message=message,
        data=data,
        status_code=status_code,
    )
