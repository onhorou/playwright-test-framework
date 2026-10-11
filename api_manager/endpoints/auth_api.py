"""Клиент эндпоинтов авторизации тестируемого приложения.

Покрывает:

- ``POST /auth/login`` — вход (и создание аккаунта при необходимости);
- ``POST /auth/logout`` — завершение сессии;
- ``GET /api/me`` — текущий аутентифицированный пользователь.

Сессионная HttpOnly-cookie сохраняется в `APIRequestContext` и автоматически
отправляется в последующих запросах того же контекста.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.api import LoginResponse, MeResponse, MessageResponse, UserCreateRequest

if TYPE_CHECKING:
    from api_manager.api_client import APIClient

__all__ = ["AuthAPI"]


class AuthAPI:
    """Эндпоинты авторизации поверх :class:`api_manager.api_client.APIClient`."""

    LOGIN_PATH = "/auth/login"
    LOGOUT_PATH = "/auth/logout"
    ME_PATH = "/api/me"

    def __init__(self, client: APIClient) -> None:
        self._client = client

    def login(self, credentials: UserCreateRequest) -> LoginResponse:
        """Войти (или зарегистрироваться) и получить профиль из ответа."""
        response = self._client.post(self.LOGIN_PATH, data=credentials.model_dump())
        return LoginResponse.model_validate(response.json())

    def logout(self) -> MessageResponse:
        """Завершить сессию (сервер сбрасывает сессионную cookie)."""
        response = self._client.post(self.LOGOUT_PATH)
        return MessageResponse.model_validate(response.json())

    def me(self) -> MeResponse:
        """Вернуть текущего аутентифицированного пользователя (``GET /api/me``)."""
        response = self._client.get(self.ME_PATH)
        return MeResponse.model_validate(response.json())
