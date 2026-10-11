"""Перечисления (enum-типы) базы данных тестируемого приложения.

Схема PostgreSQL описывает доменные значения через нативные ``ENUM``-типы.
Константы синхронизированы со схемой ``subscription-service-app`` (значения
получены из системного каталога ``pg_enum``).
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["AccessLevel", "BillingCycle", "PlanCategory", "SubscriptionStatus"]


class BillingCycle(StrEnum):
    """Периодичность списания по тарифному плану (колонка ``billing_cycle``)."""

    MONTHLY = "monthly"
    YEARLY = "yearly"


class AccessLevel(StrEnum):
    """Уровень доступа, который открывает тарифный план (колонка ``access_level``)."""

    BASIC = "basic"
    PREMIUM = "premium"
    ALL_ACCESS = "all_access"


class PlanCategory(StrEnum):
    """Категория контента тарифного плана (колонка ``category``)."""

    BOOKS = "books"
    MAGAZINES = "magazines"
    ALL = "all"


class SubscriptionStatus(StrEnum):
    """Статус подписки пользователя (колонка ``status``)."""

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
