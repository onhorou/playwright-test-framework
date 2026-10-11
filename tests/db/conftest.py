"""Локальные фикстуры DB-тестов: клиент БД, репозитории и зачистка данных.

`DBClient` создаётся на каждый тест (function-scope): соединение открывается
перед тестом и закрывается после — так изолируется состояние и повторяется
реальный жизненный цикл обращения к базе данных.

Фикстура :func:`created_users` реализует **Teardown** (зачистку данных):
тест регистрирует в ней email созданных пользователей, а после его завершения
записи удаляются из БД. Связанные подписки уходят каскадом (FK
``ON DELETE CASCADE``). Результат удаления тут же проверяется — если строка
осталась, тест помечается как ошибочный.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from config.settings import get_settings
from db_manager.crud.plan_db import PlanDB
from db_manager.crud.subscription_db import SubscriptionDB
from db_manager.crud.user_db import UserDB
from db_manager.db_client import DBClient

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def db_client() -> Iterator[DBClient]:
    """Создать клиент БД с `DB_URL` из настроек и закрыть его после теста."""
    client = DBClient(get_settings().db_url)
    client.connect()
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def user_db(db_client: DBClient) -> UserDB:
    """Репозиторий таблицы `users`, привязанный к `db_client`."""
    return UserDB(db_client)


@pytest.fixture
def plan_db(db_client: DBClient) -> PlanDB:
    """Репозиторий таблицы `plans`, привязанный к `db_client`."""
    return PlanDB(db_client)


@pytest.fixture
def subscription_db(db_client: DBClient) -> SubscriptionDB:
    """Репозиторий таблицы `subscriptions`, привязанный к `db_client`."""
    return SubscriptionDB(db_client)


@pytest.fixture
def created_users(user_db: UserDB, subscription_db: SubscriptionDB) -> Iterator[list[str]]:
    """Реестр созданных в тесте пользователей с автоматической зачисткой.

    Тест добавляет email созданного пользователя в возвращаемый список; после
    завершения теста фикстура удаляет эти записи из БД и проверяет, что
    пользователь и его подписки действительно удалены (каскад внешнего ключа).
    """
    emails: list[str] = []
    yield emails

    for email in emails:
        user = user_db.get_by_email(email)
        if user is None:
            continue
        user_id = user.id

        assert user_db.delete_by_email(email) == 1, f"Teardown: не удалось удалить {email}"
        assert user_db.get_by_email(email) is None, f"Teardown: {email} остался в БД"
        assert subscription_db.count_by_user_id(user_id) == 0, (
            f"Teardown: подписки пользователя {user_id} не удалены каскадом"
        )
