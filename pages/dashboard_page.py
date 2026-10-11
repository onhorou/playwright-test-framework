"""Page Object личного кабинета (защищённый раздел ``/dashboard``).

Страница доступна только авторизованному пользователю: без сессии сервер
отвечает редиректом на каталог (``/?login=required``). Класс описывает элементы
кабинета — email пользователя, карточку текущей подписки, блок доступа к
библиотеке — а также пустое состояние, когда подписки ещё нет.

В UI-тестах кабинет открывается без прохождения формы входа: сессия создаётся
через API и инъецируется в браузерный контекст (фикстура ``authenticated_user``
в ``tests/ui/conftest.py``).
"""

from __future__ import annotations

import allure

from pages.base_page import BasePage

__all__ = ["DashboardPage"]


class DashboardPage(BasePage):
    """Личный кабинет: текущая подписка и включённый доступ к библиотеке."""

    USER_EMAIL = "dashboard-user-email"
    SUBSCRIPTION_OVERVIEW = "subscription-overview"
    SUBSCRIPTION_PLAN = "user-subscription-plan"
    SUBSCRIPTION_STATUS = "user-subscription-status"
    SUBSCRIPTION_DAYS_REMAINING = "user-subscription-days-remaining"
    CANCEL_BUTTON = "cancel-sub-btn"
    RENEW_BUTTON = "renew-sub-btn"
    LIBRARY_ACCESS = "library-access"
    EMPTY_STATE = "subscription-empty"
    BROWSE_PLANS_LINK = "browse-plans-link"

    @allure.step("Open the dashboard")
    def open(self) -> None:
        """Открыть личный кабинет (защищённый маршрут ``/dashboard``)."""
        self.goto("/dashboard")

    def user_email(self) -> str:
        """Вернуть email, отображаемый в шапке личного кабинета."""
        return self.text(self.USER_EMAIL)

    def has_subscription(self) -> bool:
        """Проверить, что отображается карточка текущей подписки."""
        return self.is_visible(self.SUBSCRIPTION_OVERVIEW)

    def is_empty(self) -> bool:
        """Проверить пустое состояние кабинета (подписки ещё нет)."""
        return self.is_visible(self.EMPTY_STATE)

    def is_library_access_visible(self) -> bool:
        """Проверить, что отображается блок доступа к библиотеке."""
        return self.is_visible(self.LIBRARY_ACCESS)
