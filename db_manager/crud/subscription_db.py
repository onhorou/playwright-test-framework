"""CRUD-операции над таблицей ``subscriptions`` (подписки пользователей).

Внешний ключ ``subscriptions.user_id`` объявлен с ``ON DELETE CASCADE``,
поэтому удаление пользователя автоматически удаляет его подписки — это
используется фикстурой зачистки данных после тестов.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.db import Subscription, SubscriptionStatus

if TYPE_CHECKING:
    from datetime import datetime

    from db_manager.db_client import DBClient

__all__ = ["SubscriptionDB"]


class SubscriptionDB:
    """Репозиторий таблицы ``subscriptions`` поверх :class:`db_manager.db_client.DBClient`."""

    def __init__(self, client: DBClient) -> None:
        self._client = client

    def create(
        self,
        *,
        user_id: int,
        plan_id: int,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Subscription:
        """Создать подписку и вернуть созданную строку.

        ``start_date`` по умолчанию подставляется сервером (`now()`).
        Значение ``status`` приводится к доменному типу ``subscription_status``
        явным приведением в SQL, иначе PostgreSQL не сопоставит ``text`` с enum.
        """
        row = self._client.fetch_one(
            "INSERT INTO subscriptions (user_id, plan_id, status, start_date, end_date) "
            "VALUES (%s, %s, %s::subscription_status, COALESCE(%s::timestamptz, now()), "
            "%s::timestamptz) "
            "RETURNING id, user_id, plan_id, status, start_date, end_date",
            (user_id, plan_id, status.value, start_date, end_date),
        )
        if row is None:
            raise RuntimeError("INSERT ... RETURNING не вернул строку подписки.")
        return Subscription.model_validate(row)

    def get_by_id(self, subscription_id: int) -> Subscription | None:
        """Вернуть подписку по идентификатору или ``None``."""
        row = self._client.fetch_one(
            "SELECT id, user_id, plan_id, status, start_date, end_date "
            "FROM subscriptions WHERE id = %s",
            (subscription_id,),
        )
        return Subscription.model_validate(row) if row is not None else None

    def list_by_user_id(self, user_id: int) -> list[Subscription]:
        """Вернуть все подписки пользователя, отсортированные по идентификатору."""
        rows = self._client.fetch_all(
            "SELECT id, user_id, plan_id, status, start_date, end_date "
            "FROM subscriptions WHERE user_id = %s ORDER BY id",
            (user_id,),
        )
        return [Subscription.model_validate(row) for row in rows]

    def count_by_user_id(self, user_id: int) -> int:
        """Вернуть число подписок пользователя."""
        row = self._client.fetch_one(
            "SELECT count(*) AS count FROM subscriptions WHERE user_id = %s",
            (user_id,),
        )
        return int(row["count"]) if row is not None else 0

    def delete_by_user_id(self, user_id: int) -> int:
        """Удалить все подписки пользователя; вернуть число удалённых строк."""
        return self._client.execute(
            "DELETE FROM subscriptions WHERE user_id = %s",
            (user_id,),
        )
