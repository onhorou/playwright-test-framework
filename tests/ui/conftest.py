"""Локальные фикстуры UI-тестов: `base_url` контекста, Page Object'ы и Session Injection.

`base_url` браузерного контекста берётся из настроек приложения
(`get_settings().base_url`), поэтому Page Object'ы работают с относительными
путями (`page.goto("/")`), а источник URL остаётся единым — `.env` в корне
проекта (тот же, что используют API-тесты).

Фикстура :func:`authenticated_user` реализует **API-байпас авторизации**
(Session Injection): сессия создаётся запросом `POST /auth/login` в отдельном
`APIRequestContext`, а её HttpOnly-cookie `dl_session` переносится в текущий
`BrowserContext`. Благодаря этому защищённые страницы открываются сразу
авторизованными — без прохождения формы входа через UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import pytest

from api_manager.api_client import APIClient
from api_manager.endpoints.auth_api import AuthAPI
from config.settings import get_settings
from models.api import UserCreateRequest, UserResponse
from pages.dashboard_page import DashboardPage
from pages.home_page import HomePage
from pages.login_page import LoginPage

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page, Playwright


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    """Добавить `base_url` из `.env` в аргументы браузерного контекста."""
    return {**browser_context_args, "base_url": get_settings().base_url}


@pytest.fixture
def home_page(page: Page) -> HomePage:
    """Page Object главной страницы (каталог планов + шапка аккаунта)."""
    return HomePage(page)


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Page Object формы входа (drawer)."""
    return LoginPage(page)


@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    """Page Object личного кабинета (защищённый раздел `/dashboard`)."""
    return DashboardPage(page)


@pytest.fixture
def authenticated_user(playwright: Playwright, context: BrowserContext) -> UserResponse:
    """Создать пользователя через API и инъецировать его сессию в `BrowserContext`.

    Логин выполняется запросом `POST /auth/login` в отдельном `APIRequestContext`
    (API-байпас авторизации). Полученная сессионная HttpOnly-cookie `dl_session`
    переносится в текущий браузерный контекст через `context.add_cookies(...)`,
    поэтому последующие переходы открываются уже в авторизованном состоянии.
    Возвращает созданный профиль пользователя (для проверок в тесте).
    """
    request_context = playwright.request.new_context(base_url=get_settings().base_url)
    try:
        credentials = UserCreateRequest(
            email=f"user-{uuid4()}@example.com",
            full_name="Test User",
        )
        login = AuthAPI(APIClient(request_context)).login(credentials)
        # Cookie из `storage_state()` — `StorageStateCookie`, структурно идентичный
        # `SetCookieParam` из `add_cookies` (Playwright не реэкспортирует этот тип).
        cookies = cast(Any, request_context.storage_state()["cookies"])
        context.add_cookies(cookies)
        return login.user
    finally:
        request_context.dispose()
