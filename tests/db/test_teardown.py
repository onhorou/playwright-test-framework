"""Check/Verify для M6: работа с БД и зачистка данных (Teardown).

Тесты проверяют DB-слой фреймворка: подключение и выполнение запросов через
:class:`db_manager.db_client.DBClient`, CRUD-репозитории
(:mod:`db_manager.crud`) и валидацию строк Pydantic-схемами :mod:`models.db`.
Отдельно проверяется автоматическая зачистка созданных сущностей фикстурой
`created_users` (в том числе каскадное удаление подписок).
"""

from __future__ import annotations

from uuid import uuid4

import allure
import pytest

from db_manager.crud.plan_db import PlanDB
from db_manager.crud.subscription_db import SubscriptionDB
from db_manager.crud.user_db import UserDB
from models.db import SubscriptionStatus

pytestmark = pytest.mark.regression


def _unique_email() -> str:
    """Сгенерировать уникальный email тестового пользователя."""
    return f"db-{uuid4()}@example.com"


@allure.feature("Database")
@allure.story("Users CRUD")
@allure.title("Created user is stored in the database")
def test_created_user_is_stored_in_database(
    user_db: UserDB,
    created_users: list[str],
) -> None:
    """Запись, созданная через CRUD, читается из БД и валидируется схемой.

    Пользователь регистрируется в `created_users`, поэтому после теста будет
    автоматически удалён (проверка зачистки — в teardown фикстуры).
    """
    email = _unique_email()
    created_users.append(email)

    created = user_db.create(email=email, full_name="DB Test User")
    stored = user_db.get_by_email(email)

    assert stored is not None
    assert stored.id == created.id
    assert stored.email == email
    assert stored.full_name == "DB Test User"


@pytest.mark.smoke
@allure.feature("Database")
@allure.story("Catalogue")
@allure.title("Plans are read from the database")
def test_plans_are_read_from_database(plan_db: PlanDB) -> None:
    """Справочник тарифных планов читается из БД и валидируется схемой."""
    plans = plan_db.list_all()

    assert plans, "Справочник plans пуст — приложение не засеяло данные"
    assert all(plan.id > 0 for plan in plans)


@allure.feature("Database")
@allure.story("Teardown")
@allure.title("Subscription is deleted with its user on teardown")
def test_subscription_is_deleted_with_user_on_teardown(
    user_db: UserDB,
    plan_db: PlanDB,
    subscription_db: SubscriptionDB,
    created_users: list[str],
) -> None:
    """Подписка пользователя удаляется каскадом при зачистке данных (teardown).

    В конце теста `created_users` удалит пользователя и проверит, что связанные
    с ним подписки также исчезли (FK `ON DELETE CASCADE`).
    """
    email = _unique_email()
    created_users.append(email)

    user = user_db.create(email=email, full_name="DB Cascade User")
    plan = plan_db.list_all()[0]

    subscription = subscription_db.create(
        user_id=user.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
    )

    assert subscription.user_id == user.id
    assert subscription.plan_id == plan.id
    assert subscription.status is SubscriptionStatus.ACTIVE
    assert subscription_db.count_by_user_id(user.id) == 1
