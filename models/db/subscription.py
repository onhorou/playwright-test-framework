"""Pydantic-схема строки таблицы ``subscriptions`` (подписка пользователя на план).

Сущность соответствует плановому ``bookings`` из исходной структуры проекта:
в реальном приложении «бронирования» называются подписками (``subscriptions``).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models.db.enums import SubscriptionStatus

__all__ = ["Subscription"]


class Subscription(BaseModel):
    """Строка таблицы ``subscriptions``."""

    id: int = Field(..., description="Первичный ключ записи.")
    user_id: int = Field(..., description="Внешний ключ на ``users.id``.")
    plan_id: int = Field(..., description="Внешний ключ на ``plans.id``.")
    status: SubscriptionStatus = Field(..., description="Текущий статус подписки.")
    start_date: datetime = Field(..., description="Дата начала подписки.")
    end_date: datetime | None = Field(
        None,
        description="Дата окончания подписки (``None`` — если не задана).",
    )
