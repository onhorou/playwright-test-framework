"""Pydantic-DTO для HTTP-API тестируемого приложения.

Реэкспортирует схемы авторизации и пользователя для удобного импорта::

    from models.api import LoginResponse, UserCreateRequest, UserResponse
"""

from models.api.auth import LoginResponse, MeResponse, MessageResponse
from models.api.user import UserCreateRequest, UserResponse

__all__ = [
    "LoginResponse",
    "MeResponse",
    "MessageResponse",
    "UserCreateRequest",
    "UserResponse",
]
