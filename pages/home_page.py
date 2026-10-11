"""Page Object главной страницы приложения (каталог планов + header).

Страница каталога одновременно содержит шапку с состоянием аккаунта:
в анонимном виде — кнопку ``login-open-btn``, после входа — меню пользователя
с email (``user-menu`` / ``user-email``) и ссылку на дашборд
(``dashboard-link``). Класс описывает эти элементы и переход к форме входа.
"""

from __future__ import annotations

from pages.base_page import BasePage
from pages.login_page import LoginPage

__all__ = ["HomePage"]


class HomePage(BasePage):
    """Каталог планов и шапка с состоянием аккаунта."""

    LOGIN_OPEN_BUTTON = "login-open-btn"
    USER_MENU = "user-menu"
    USER_EMAIL = "user-email"
    DASHBOARD_LINK = "dashboard-link"

    def open(self) -> None:
        """Открыть страницу каталога (корневой маршрут приложения)."""
        self.goto("/")

    def is_authenticated(self) -> bool:
        """Проверить, что шапка отображает авторизованного пользователя."""
        return self.is_visible(self.USER_MENU)

    def wait_until_authenticated(self) -> None:
        """Дождаться перехода шапки в авторизованное состояние."""
        self.wait_for_visible(self.USER_MENU)

    def user_email(self) -> str:
        """Вернуть email текущего авторизованного пользователя из шапки."""
        return self.text(self.USER_EMAIL)

    def open_login_drawer(self) -> None:
        """Открыть панель входа кликом по кнопке в шапке и дождаться её появления."""
        self.click(self.LOGIN_OPEN_BUTTON)
        LoginPage(self.page).open()
