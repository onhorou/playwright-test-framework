"""Pydantic-схема строки таблицы ``users``.

Описывает аккаунт пользователя так, как он хранится в базе данных.
Отличается от API-DTO :class:`models.api.user.UserResponse` наличием
служебной колонки ``created_at``.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

__all__ = ["User"]


class User(BaseModel):
    """Строка таблицы ``users``."""

    id: int = Field(..., description="Первичный ключ записи.")
    email: str = Field(..., description="Уникальный email пользователя.")
    full_name: str = Field(..., description="Полное имя пользователя.")
    created_at: datetime = Field(..., description="Момент создания записи.")
