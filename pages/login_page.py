"""Page Object формы входа (slide-over drawer) тестируемого приложения.

В приложении нет отдельного маршрута ``/login``: вход выполняется в выдвижной
панели (drawer) на странице каталога. Класс описывает элементы этой панели и
сценарий входа. Открывается панель через
:meth:`pages.home_page.HomePage.open_login_drawer`.

Состояние панели отражается атрибутом ``data-state="open"`` / ``"closed"``;
в закрытом виде элемент скрыт классом ``hidden``.
"""

from __future__ import annotations

from pages.base_page import BasePage

__all__ = ["LoginPage"]


class LoginPage(BasePage):
    """Элементы и действия формы входа в drawer'е."""

    DRAWER = "login-drawer"
    EMAIL_INPUT = "login-email-input"
    NAME_INPUT = "login-name-input"
    SUBMIT_BUTTON = "login-submit-btn"
    ERROR = "login-error"

    def open(self) -> None:
        """Дождаться, пока панель входа станет видимой (открытой)."""
        self.wait_for_visible(self.DRAWER)

    def is_open(self) -> bool:
        """Проверить, что панель входа находится в открытом состоянии."""
        return self.attribute(self.DRAWER, "data-state") == "open"

    def fill_credentials(self, email: str, full_name: str) -> None:
        """Заполнить поля email и полного имени."""
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.NAME_INPUT, full_name)

    def submit(self) -> None:
        """Отправить форму входа."""
        self.click(self.SUBMIT_BUTTON)

    def login(self, email: str, full_name: str) -> None:
        """Выполнить вход: заполнить форму и отправить её."""
        self.fill_credentials(email, full_name)
        self.submit()

    def error_text(self) -> str:
        """Вернуть текст сообщения об ошибке входа (если оно показано)."""
        return self.text(self.ERROR)
