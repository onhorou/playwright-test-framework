"""CRUD-операции над таблицей ``plans`` (справочник тарифных планов).

Справочник наполняется приложением (сиды) и в тестах используется только для
чтения: планы нужны как валидные ``plan_id`` при создании подписок.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.db import Plan

if TYPE_CHECKING:
    from db_manager.db_client import DBClient

__all__ = ["PlanDB"]


class PlanDB:
    """Репозиторий таблицы ``plans`` поверх :class:`db_manager.db_client.DBClient`."""

    def __init__(self, client: DBClient) -> None:
        self._client = client

    def list_all(self) -> list[Plan]:
        """Вернуть все тарифные планы, отсортированные по идентификатору."""
        rows = self._client.fetch_all(
            "SELECT id, name, price, billing_cycle, access_level, category FROM plans ORDER BY id"
        )
        return [Plan.model_validate(row) for row in rows]

    def get_by_id(self, plan_id: int) -> Plan | None:
        """Вернуть тарифный план по идентификатору или ``None``."""
        row = self._client.fetch_one(
            "SELECT id, name, price, billing_cycle, access_level, category "
            "FROM plans WHERE id = %s",
            (plan_id,),
        )
        return Plan.model_validate(row) if row is not None else None

    def get_by_name(self, name: str) -> Plan | None:
        """Вернуть тарифный план по уникальному названию или ``None``."""
        row = self._client.fetch_one(
            "SELECT id, name, price, billing_cycle, access_level, category "
            "FROM plans WHERE name = %s",
            (name,),
        )
        return Plan.model_validate(row) if row is not None else None
