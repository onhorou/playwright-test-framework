# playwright-test-framework

Test automation framework for the **subscription-service-app** (API + UI + DB),
built with **Playwright**, **Pytest** and **Poetry**.

## Stack

- **Python 3.13** (pinned in `.python-version`)
- **Poetry** 2.x — dependency and environment management
- **Pytest** + **pytest-playwright** — test runner and Playwright fixtures
- **Pydantic v2** + **pydantic-settings** — DTOs and configuration
- **Loguru** — logging
- **Ruff** — linter and formatter
- **Mypy** — static type checking
- **pre-commit** — git hooks

## Requirements

- Python 3.13
- Poetry 2.x

## Setup

```bash
# create (or reuse) the virtualenv with Python 3.13 and install dependencies
poetry env use python3.13
poetry install

# install git hooks (ruff + mypy run before every commit)
poetry run pre-commit install
```

## Configuration

Настройки читаются из переменных окружения (`config/settings.py`, на базе `pydantic-settings`).
Создайте файл `.env` в корне проекта по шаблону `.env.example`:

```bash
cp .env.example .env
```

| Переменная | Назначение | Пример |
|------------|-----------|--------|
| `BASE_URL` | Базовый URL тестируемого приложения | `http://localhost:8000` |
| `DB_URL`   | Строка подключения к базе данных PostgreSQL | `postgresql://user:password@localhost:5432/database` |

Файл `.env` не коммитится в Git. В коде настройки получаются через фабрику `get_settings()`
(кэшируется через `lru_cache`):

```python
from config.settings import get_settings

settings = get_settings()
settings.base_url
settings.db_url
```

## Logging

Логирование построено на **loguru** (`utils/logger.py`). Инициализация выполняется
один раз за тестовую сессию в `tests/conftest.py` (`setup_logging()`):

- цветной вывод в `stdout`;
- запись в файл `logs/framework.log` с ротацией (`10 MB`), сжатием (`zip`) и
  удалением файлов старше `10 days`.

Получить логгер и привязать метаданные к логам блока:

```python
from utils.logger import log_context, logger

logger.info("Старт сценария")

with log_context(user_id=42, booking_id="bk-1"):
    logger.info("Бронирование создано")  # в логе появится user_id=42 booking_id=bk-1
```

Для каждого теста логи автоматически перехватываются и прикрепляются к отчёту Allure
(как только подключён `allure-pytest`).

## API layer

API-тесты работают поверх нативного `APIRequestContext` из Playwright — отдельной
HTTP-библиотеки (например, `requests`) в проекте нет.

- `models/api/` — Pydantic-DTO:
  - `UserCreateRequest` — тело запроса `POST /auth/login` (создаёт аккаунт при первом входе);
  - `UserResponse` — профиль пользователя (`id`, `email`, `full_name`);
  - `LoginResponse`, `MeResponse`, `MessageResponse` — ответы авторизации.
- `api_manager/api_client.py` — `APIClient`, базовая обёртка над `APIRequestContext`
  (методы `get`/`post`/`put`/`patch`/`delete`, логирование метода, URL и статуса).
- `api_manager/endpoints/auth_api.py` — `AuthAPI` с методами `login()`, `logout()`, `me()`.

Авторизация в приложении — **сессионная HttpOnly-cookie** (`dl_session`), а не
bearer-токен: сервер ставит cookie заголовком `Set-Cookie`, а Playwright-контекст
автоматически отправляет её в последующих запросах.

Фикстуры `api_client` и `auth_api` определены в `tests/api/conftest.py`.
`APIRequestContext` создаётся на каждый тест (изоляция сессионных cookie).

```bash
poetry run pytest tests/api/   # только API-тесты
```

## Linting & type checking

Инструменты качества кода настраиваются в `pyproject.toml`:

- **ruff** (`[tool.ruff]`) — линтер и сортировка импортов; набор правил
  `E, W, F, I, PT, S` (PEP 8, Pyflakes, isort, pytest-style, bandit).
  Для тестов правило `S101` (`assert`) отключено.
- **mypy** (`[tool.mypy]`) — статическая типизация: включён режим `strict` и
  плагин `pydantic.mypy`; для пакета `tests.*` аннотации типов не обязательны.

```bash
poetry run ruff check .      # линтинг
poetry run ruff format .     # автоформатирование
poetry run mypy .            # проверка типов
```

Хуки pre-commit (`.pre-commit-config.yaml`) прогоняют ruff и mypy перед каждым
коммитом (инструменты берутся из Poetry-окружения):

```bash
poetry run pre-commit run --all-files   # запустить хуки вручную по всем файлам
```

## Run tests

```bash
poetry run pytest
```
