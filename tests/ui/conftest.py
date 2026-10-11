"""Локальные фикстуры UI-тестов: `base_url` контекста и Page Object'ы.

`base_url` браузерного контекста берётся из настроек приложения
(`get_settings().base_url`), поэтому Page Object'ы работают с относительными
путями (`page.goto("/")`), а источник URL остаётся единым — `.env` в корне
проекта (тот же, что используют API-тесты).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from config.settings import get_settings
from pages.home_page import HomePage
from pages.login_page import LoginPage

if TYPE_CHECKING:
    from playwright.sync_api import Page


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
