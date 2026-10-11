"""Pydantic-DTO пользователя для API тестируемого приложения.

Аккаунт создаётся эндпоинтом ``POST /auth/login`` при первом входе,
поэтому запрос на вход совпадает с запросом на создание пользователя.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["UserCreateRequest", "UserResponse"]


class UserCreateRequest(BaseModel):
    """Тело запроса ``POST /auth/login`` (создаёт аккаунт при необходимости)."""

    email: str = Field(
        ...,
        min_length=1,
        description="Email пользователя; используется как уникальный идентификатор.",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        description="Полное имя пользователя.",
    )


class UserResponse(BaseModel):
    """Профиль пользователя в ответах API (``/auth/login``, ``/api/me``)."""

    id: int = Field(..., description="Идентификатор пользователя в базе данных.")
    email: str = Field(..., description="Email пользователя.")
    full_name: str = Field(..., description="Полное имя пользователя.")
