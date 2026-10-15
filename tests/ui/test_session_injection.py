"""Check/Verify для M5: API-байпас авторизации для UI (Session Injection).

Сессия создаётся через API (`POST /auth/login`) и инъецируется в браузерный
контекст фикстурой `authenticated_user`, поэтому защищённый раздел
(`/dashboard`) открывается сразу в авторизованном состоянии — без прохождения
формы входа через UI. Негативный сценарий проверяет, что без сессии доступ к
разделу невозможен и посетитель перенаправляется на каталог.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import allure
import pytest

from models.api import UserResponse
from pages.dashboard_page import DashboardPage
from pages.home_page import HomePage

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.regression


@pytest.mark.smoke
@allure.feature("Authentication")
@allure.story("Session injection")
@allure.title("Dashboard opens with an API-injected session")
def test_dashboard_opens_with_api_injected_session(
    authenticated_user: UserResponse,
    home_page: HomePage,
    dashboard_page: DashboardPage,
) -> None:
    """Защищённый раздел открывается сразу авторизованным, минуя форму входа."""
    dashboard_page.open()

    assert dashboard_page.user_email() == authenticated_user.email
    assert home_page.is_authenticated() is True
    assert home_page.user_email() == authenticated_user.email
    assert dashboard_page.is_empty() is True


@allure.feature("Authentication")
@allure.story("Session injection")
@allure.title("Dashboard redirects an anonymous visitor")
def test_dashboard_redirects_anonymous_visitor(
    home_page: HomePage,
    dashboard_page: DashboardPage,
    page: Page,
) -> None:
    """Без сессии `/dashboard` перенаправляет на каталог (``?login=required``)."""
    dashboard_page.open()

    assert page.url.endswith("/?login=required")
    assert home_page.is_authenticated() is False
