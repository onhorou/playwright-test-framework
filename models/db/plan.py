"""Pydantic-схема строки таблицы ``plans`` (тарифный план библиотеки)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from models.db.enums import AccessLevel, BillingCycle, PlanCategory

__all__ = ["Plan"]


class Plan(BaseModel):
    """Строка таблицы ``plans``."""

    id: int = Field(..., description="Первичный ключ записи.")
    name: str = Field(..., description="Уникальное название тарифного плана.")
    price: Decimal = Field(..., description="Стоимость плана.")
    billing_cycle: BillingCycle = Field(..., description="Периодичность списания.")
    access_level: AccessLevel = Field(..., description="Уровень доступа по плану.")
    category: PlanCategory = Field(..., description="Категория контента плана.")
