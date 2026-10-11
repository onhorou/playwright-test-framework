"""Check/Verify для M4: вход пользователя через UI и работа Page Object Model.

Проверяются базовый класс :class:`pages.base_page.BasePage`, Page Object'ы
:class:`pages.home_page.HomePage` и :class:`pages.login_page.LoginPage`:
каталог открывается в анонимном состоянии, форма входа в drawer'е авторизует
пользователя, после чего шапка переходит в авторизованный вид.
"""

from __future__ import annotations

from uuid import uuid4

from pages.home_page import HomePage
from pages.login_page import LoginPage


def test_login_via_ui_reaches_authenticated_state(
    home_page: HomePage,
    login_page: LoginPage,
) -> None:
    """Вход через drawer авторизует пользователя и показывает его email в шапке."""
    email = f"user-{uuid4()}@example.com"
    full_name = "Test User"

    home_page.open()
    assert home_page.is_authenticated() is False

    home_page.open_login_drawer()
    assert login_page.is_open() is True
    login_page.login(email, full_name)

    home_page.wait_until_authenticated()
    assert home_page.is_authenticated() is True
    assert home_page.user_email() == email
    assert home_page.is_visible(HomePage.DASHBOARD_LINK) is True
