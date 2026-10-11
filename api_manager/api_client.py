"""Базовый HTTP-клиент API-тестов поверх Playwright `APIRequestContext`.

:class:`APIClient` — тонкая обёртка, которая ничего не знает о конкретных
эндпоинтах: она выполняет HTTP-запросы и единообразно логирует метод, URL
и код ответа. Транспорт — нативный `APIRequestContext` из Playwright
(общий стек с UI-контекстом, без отдельной библиотеки вроде `requests`).

Клиенты конкретных сущностей группируются в пакете :mod:`api_manager.endpoints`
и получают экземпляр :class:`APIClient` в конструктор.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import allure

from utils.logger import logger

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext, APIResponse

__all__ = ["APIClient"]


class APIClient:
    """Обёртка над `APIRequestContext` с единым логированием запросов."""

    def __init__(self, request_context: APIRequestContext) -> None:
        self._request = request_context

    @property
    def request(self) -> APIRequestContext:
        """Нижележащий `APIRequestContext`.

        Доступен для работы с сессионными cookie/storage state (например,
        для переноса сессии из API в UI-контекст в M5).
        """
        return self._request

    @allure.step("GET {url}")
    def get(self, url: str, **kwargs: Any) -> APIResponse:
        """Выполнить ``GET``-запрос и вернуть ответ."""
        return self._send("GET", self._request.get, url, **kwargs)

    @allure.step("POST {url}")
    def post(self, url: str, **kwargs: Any) -> APIResponse:
        """Выполнить ``POST``-запрос и вернуть ответ."""
        return self._send("POST", self._request.post, url, **kwargs)

    @allure.step("PUT {url}")
    def put(self, url: str, **kwargs: Any) -> APIResponse:
        """Выполнить ``PUT``-запрос и вернуть ответ."""
        return self._send("PUT", self._request.put, url, **kwargs)

    @allure.step("PATCH {url}")
    def patch(self, url: str, **kwargs: Any) -> APIResponse:
        """Выполнить ``PATCH``-запрос и вернуть ответ."""
        return self._send("PATCH", self._request.patch, url, **kwargs)

    @allure.step("DELETE {url}")
    def delete(self, url: str, **kwargs: Any) -> APIResponse:
        """Выполнить ``DELETE``-запрос и вернуть ответ."""
        return self._send("DELETE", self._request.delete, url, **kwargs)

    @staticmethod
    def _send(
        method: str,
        handler: Callable[..., APIResponse],
        url: str,
        **kwargs: Any,
    ) -> APIResponse:
        """Выполнить запрос через `handler` и залогировать его результат."""
        response = handler(url, **kwargs)
        logger.debug(
            "API {method} {url} -> {status}",
            method=method,
            url=url,
            status=response.status,
        )
        return response
