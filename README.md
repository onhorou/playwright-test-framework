# playwright-test-framework

Test automation framework for the **subscription-service-app** (API + UI + DB),
built with **Playwright**, **Pytest** and **Poetry**.

## Stack

- **Python 3.13** (pinned in `.python-version`)
- **Poetry** 2.x — dependency and environment management
- **Pytest** + **pytest-playwright** — test runner and Playwright fixtures
- **Pydantic v2** + **pydantic-settings** — DTOs and configuration
- **psycopg 3** — PostgreSQL client for DB tests
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

# download the Chromium browser used by UI tests (one-off)
poetry run playwright install chromium
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

## UI layer

UI-тесты построены на паттерне **Page Object Model (POM)** и нативных фикстурах
Playwright (`pytest-playwright`).

- `pages/base_page.py` — `BasePage`, базовая обёртка над `Page`: навигация и
  операции над элементами по атрибуту `data-testid`.
- `pages/home_page.py` — `HomePage`, каталог планов и шапка с состоянием аккаунта.
- `pages/login_page.py` — `LoginPage`, форма входа (slide-over drawer).

В приложении нет отдельного маршрута входа: кнопка **Sign In / Register** в шапке
открывает панель входа. После успешного входа шапка показывает email пользователя
и ссылку на дашборд.

Фикстуры UI-тестов определены в `tests/ui/conftest.py`. `base_url` браузерного
контекста берётся из настроек (`get_settings().base_url`), поэтому Page Object'ы
работают с относительными путями, а источник URL остаётся единым — `.env`.

```bash
# один раз установите браузер
poetry run playwright install chromium

poetry run pytest tests/ui/            # UI-тесты (headless)
poetry run pytest --headed tests/ui/   # с видимым окном браузера
```

### Session injection (API → UI)

Защищённые разделы (например, `/dashboard`) UI-тесты открывают без прохождения
формы входа: сессия создаётся через API и инъецируется в браузерный контекст.

- Фикстура `authenticated_user` (`tests/ui/conftest.py`) выполняет
  `POST /auth/login` в отдельном `APIRequestContext`, получает сессионную
  HttpOnly-cookie `dl_session` и переносит её в текущий `BrowserContext`
  (`context.add_cookies`). Фикстура возвращает профиль пользователя.
- `pages/dashboard_page.py` — `DashboardPage`, Page Object личного кабинета
  (email пользователя, карточка подписки, доступ к библиотеке, пустое состояние).

```python
def test_dashboard_opens_with_api_injected_session(authenticated_user, dashboard_page, home_page):
    dashboard_page.open()  # защищённый раздел сразу авторизован
    assert home_page.user_email() == authenticated_user.email
```

Без сессии `/dashboard` перенаправляет анонимного посетителя на каталог
(`/?login=required`) — это проверяет отдельный негативный тест.

## Database layer

DB-тесты работают с PostgreSQL напрямую через **psycopg 3**; подключение и SQL
инкапсулированы в слое `db_manager/`.

- `models/db/` — Pydantic-схемы таблиц: `User` (`users`), `Plan` (`plans`),
  `Subscription` (`subscriptions`) и enum-типы (`BillingCycle`, `AccessLevel`,
  `PlanCategory`, `SubscriptionStatus`).
- `db_manager/db_client.py` — `DBClient`, обёртка над соединением `psycopg`
  (`dict_row`, `autocommit`, логирование запросов). Строки возвращаются
  словарями и валидируются схемами из `models.db`.
- `db_manager/crud/` — репозитории таблиц по сущностям: `UserDB`, `PlanDB`,
  `SubscriptionDB` (методы `create` / `get_*` / `count_*` / `delete_*`).

Фикстуры DB-тестов определены в `tests/db/conftest.py`: `db_client`, `user_db`,
`plan_db`, `subscription_db`. Соединение открывается на каждый тест и
закрывается после него.

### Data teardown

Фикстура `created_users` реализует автоматическую **зачистку данных**: тест
регистрирует в ней email созданных сущностей, а после завершения теста они
удаляются из БД. Связанные подписки удаляются каскадом (внешний ключ
`ON DELETE CASCADE`). Результат удаления проверяется сразу — если запись
осталась, тест помечается как ошибочный.

```python
def test_created_user_is_stored_in_database(user_db, created_users):
    email = "db-user@example.com"
    created_users.append(email)  # запись будет удалена после теста

    created = user_db.create(email=email, full_name="DB Test User")
    assert user_db.get_by_email(email).id == created.id
```

```bash
poetry run pytest tests/db/   # только DB-тесты
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
