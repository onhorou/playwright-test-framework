"""Check/Verify для M3: создание и авторизация пользователя через API.

Проверяет первый API-клиент (:class:`APIClient`), клиент эндпоинтов
(:class:`AuthAPI`) и Pydantic-DTO из :mod:`models.api`.
"""

from __future__ import annotations

from uuid import uuid4

from api_manager.api_client import APIClient
from api_manager.endpoints.auth_api import AuthAPI
from models.api import LoginResponse, MeResponse, MessageResponse, UserCreateRequest


def _unique_credentials() -> UserCreateRequest:
    """Сгенерировать данные нового уникального пользователя."""
    return UserCreateRequest(
        email=f"user-{uuid4()}@example.com",
        full_name="Test User",
    )


def test_login_creates_account_and_returns_profile(auth_api: AuthAPI) -> None:
    """`POST /auth/login` создаёт пользователя и возвращает его профиль."""
    credentials = _unique_credentials()

    login: LoginResponse = auth_api.login(credentials)

    assert login.ok is True
    assert login.user.id > 0
    assert login.user.email == credentials.email
    assert login.user.full_name == credentials.full_name


def test_session_cookie_allows_accessing_current_user(auth_api: AuthAPI) -> None:
    """После входа `GET /api/me` отдаёт того же пользователя (по cookie)."""
    created = auth_api.login(_unique_credentials())

    me: MeResponse = auth_api.me()

    assert me.ok is True
    assert me.user == created.user


def test_me_requires_authentication(api_client: APIClient) -> None:
    """Без сессии `GET /api/me` отвечает `401 Not authenticated`."""
    response = api_client.get("/api/me")

    assert response.status == 401
    body = MessageResponse.model_validate(response.json())
    assert body.ok is False
    assert body.message == "Not authenticated."


def test_login_requires_email_and_full_name(api_client: APIClient) -> None:
    """`POST /auth/login` без обязательных полей отвечает `422`."""
    response = api_client.post("/auth/login", data={"email": "", "full_name": ""})

    assert response.status == 422
    body = MessageResponse.model_validate(response.json())
    assert body.ok is False
    assert "required" in body.message.lower()


def test_logout_clears_session(auth_api: AuthAPI, api_client: APIClient) -> None:
    """`POST /auth/logout` сбрасывает сессию — `/api/me` снова отдаёт `401`."""
    auth_api.login(_unique_credentials())

    logout: MessageResponse = auth_api.logout()

    assert logout.ok is True
    assert api_client.get("/api/me").status == 401
