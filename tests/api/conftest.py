"""Локальные фикстуры API-тестов: HTTP-клиент и клиенты эндпоинтов.

`APIRequestContext` создаётся на каждый тест (function-scope): это изолирует
сессионные cookie между тестами и повторяет рабочий режим одного пользователя.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import APIRequestContext

from api_manager.api_client import APIClient
from api_manager.endpoints.auth_api import AuthAPI
from config.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playwright.sync_api import Playwright


@pytest.fixture
def api_client(playwright: Playwright) -> Iterator[APIClient]:
    """Создать HTTP-клиент с `base_url` из настроек и закрыть его после теста."""
    request_context: APIRequestContext = playwright.request.new_context(
        base_url=get_settings().base_url,
    )
    try:
        yield APIClient(request_context)
    finally:
        request_context.dispose()


@pytest.fixture
def auth_api(api_client: APIClient) -> AuthAPI:
    """Клиент эндпоинтов авторизации, привязанный к `api_client`."""
    return AuthAPI(api_client)
