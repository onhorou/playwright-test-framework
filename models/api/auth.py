"""Pydantic-DTO авторизации (``/auth/login``, ``/auth/logout``, ``/api/me``).

Тестируемое приложение аутентифицирует клиента **сессионной HttpOnly-cookie**
(``dl_session``), а не bearer-токеном: сервер ставит cookie заголовком
``Set-Cookie``, а в теле ответа токена нет. Поэтому «плановый» DTO
``AuthTokenResponse`` заменён на :class:`LoginResponse` — см. ``systemPatterns.md``.
"""

from __future__ import annotations

from pydantic import BaseModel

from models.api.user import UserResponse

__all__ = ["LoginResponse", "MeResponse", "MessageResponse"]


class MessageResponse(BaseModel):
    """Ответ вида ``{"ok": ..., "message": ...}``.

    Используется для ``POST /auth/logout`` и для тел ошибок (``401``/``422``).
    """

    ok: bool
    message: str


class LoginResponse(BaseModel):
    """Успешный ответ ``POST /auth/login`` (сессионная cookie ставится сервером)."""

    ok: bool
    message: str
    user: UserResponse


class MeResponse(BaseModel):
    """Успешный ответ ``GET /api/me`` — текущий пользователь сессии."""

    ok: bool
    user: UserResponse
