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
- **pytest-xdist** + **filelock** — parallel execution and cross-process isolation
- **Allure** (allure-pytest) — test reporting: features/stories, steps, failure screenshots
- **Docker** + **Docker Compose** — containerised test run against the target app
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

При параллельном запуске (`pytest-xdist`) каждый процесс пишет в собственный
файл `logs/framework-<worker_id>.log` — процессы не мешают друг другу.

Получить логгер и привязать метаданные к логам блока:

```python
from utils.logger import log_context, logger

logger.info("Старт сценария")

with log_context(user_id=42, booking_id="bk-1"):
    logger.info("Бронирование создано")  # в логе появится user_id=42 booking_id=bk-1
```

Для каждого теста логи автоматически перехватываются и прикрепляются к отчёту Allure
(см. раздел [Reporting](#reporting-allure)).

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

## Parallel execution & process isolation

Тесты можно запускать в несколько процессов `pytest-xdist`:

```bash
poetry run pytest -n 3          # 3 воркера
poetry run pytest -n auto       # число воркеров = числу CPU
```

Изоляция процессов обеспечивается на двух уровнях:

- **Логи не пересекаются.** Каждый воркер пишет в собственный файл
  `logs/framework-<worker_id>.log` (при обычном запуске — `logs/framework.log`).
  Имя файла формирует `utils/logger.log_file_for_worker()`, а применяет
  сессионная фикстура `_configure_logging` (`tests/conftest.py`). Так исключается
  одновременная запись и ротация одного файла несколькими процессами.
- **Общие артефакты защищены `FileLock`.** Сессионная фикстура `run_manifest`
  ведёт общий для всех воркеров манифест `logs/run.json` (идентификатор запуска,
  время старта, список воркеров). Цикл «прочитать → изменить → записать» одного
  файла несколькими процессами — это гонка (Race Conditions); `filelock.FileLock`
  сериализует доступ, поэтому манифест остаётся консистентным. Манифест
  обнуляется при смене запуска (`PYTEST_XDIST_TESTRUNUID`) и отражает только
  текущую сессию.

```python
from filelock import FileLock


@pytest.fixture(scope="session")
def run_manifest(worker_id: str) -> dict[str, Any]:
    with FileLock(f"{RUN_MANIFEST_FILE}.lock"):
        ...  # критическая секция: общий файл изменяется под блокировкой
```

## Reporting (Allure)

Отчётность построена на плагине **allure-pytest**. Результаты любого запуска
складываются в `allure-results/` — это задано в `pytest.ini`, поэтому отдельно
передавать флаг не нужно:

```ini
[pytest]
addopts = --alluredir=allure-results --clean-alluredir
```

Чтобы получить HTML-отчёт, нужен **Allure CLI** (требуется Java 11+):

```bash
# установить CLI (один раз)
npm install -g allure-commandline

# или запускать разово без установки
npx allure-commandline --help

# перегенерить отчет в /allure-report
npx allure-commandline generate --clean
```

```bash
poetry run pytest                                        # прогон пишет allure-results/
allure generate allure-results -o allure-report --clean  # статический HTML-отчёт
allure serve allure-results                              # локальный сервер с авто-обновлением
```

Что попадает в отчёт:

- **структура Features → Stories → Tests** — аннотации `@allure.feature`,
  `@allure.story`, `@allure.title` в тестах;
- **пошаговое выполнение** — декораторы `@allure.step` в Page Object'ах
  (`pages/`) и API-клиентах (`api_manager/`); вложенные шаги показывают, на
  каком бизнес-действии упал тест;
- **скриншот и URL страницы при падении UI-теста** — хук
  `pytest_runtest_makereport` (`tests/conftest.py`) автоматически прикладывает
  вложения `screenshot-on-failure` (`full_page`) и `url-on-failure`;
- **логи loguru по каждому тесту** — фикстура `_capture_logs` прикладывает
  перехваченные логи вложением `loguru logs — <test>`.

Пример аннотаций:

```python
import allure


@allure.feature("Authentication")
@allure.story("Login")
@allure.title("Login creates an account and returns the profile")
def test_login_creates_account_and_returns_profile(auth_api: AuthAPI) -> None:
    # arrange → act → assert над бизнес-действиями API-клиента / Page Object
    ...
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
poetry run pytest            # вся тестовая сессия
poetry run pytest -n 3       # параллельно, в 3 процесса (pytest-xdist)
```

Каждый запуск пишет результаты Allure в `allure-results/` — как посмотреть отчёт,
см. раздел [Reporting](#reporting-allure).

## Containerization (Docker & Docker Compose)

Тесты можно запускать целиком в контейнерах — вместе с приложением-мишенью и его
базой данных. Это убирает ручную подготовку окружения: достаточно Docker.

| Файл | Назначение |
|------|-----------|
| `Dockerfile` | образ тестового фреймворка (сервис `tests`) |
| `docker-compose.yml` | оркестрация трёх сервисов в общей сети Compose |
| `.dockerignore` | что не попадает в контекст сборки (`.git`, `.venv`, `.env`, артефакты, ...) |

`docker-compose.yml` поднимает:

- **`postgres_db`** — БД приложения (`postgres:16-alpine`), доступна тестам по имени
  сервиса (`postgres_db:5432`);
- **`webapp`** — приложение-мишень `subscription-service-app`. Образ собирается
  **напрямую из Git-репозитория** (`build.context` — Git-URL), поэтому локальный
  клон приложения не нужен: BuildKit сам клонирует контекст сборки. Перед стартом
  сервера контейнер применяет миграции (`alembic upgrade head`);
- **`tests`** — образ фреймворка, который запускает `pytest` против приложения и БД.

Сервис `tests` стартует только после того, как `webapp` пройдёт healthcheck
(`/healthz`), а тот, в свою очередь, — после готовности `postgres_db`
(`condition: service_healthy`). URL и строка подключения передаются контейнеру
через переменные окружения `BASE_URL=http://webapp:8000` и
`DB_URL=postgresql://...@postgres_db:5432/...` — тот же контракт, что и локально
(см. [Configuration](#configuration)).

> Сервис приложения назван `webapp`, а не `app`, намеренно: `app` — это
> HSTS-preloaded TLD, поэтому Chromium принудительно переводит `http://app` на
> HTTPS и UI-тесты падают с `net::ERR_SSL_PROTOCOL_ERROR`.

### Test image (Dockerfile)

Образ построен на `mcr.microsoft.com/playwright/python`, причём тег **жёстко
привязан к версии Playwright из `poetry.lock`**:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble
```

Версия в теге должна совпадать с Python-зависимостью `playwright` — иначе
Playwright не найдёт исполняемые файлы браузеров. В образе уже есть
`chromium`/`firefox`/`webkit` и их системные зависимости, поэтому отдельная
установка браузеров (`playwright install`) не требуется.

Базовый образ содержит Python 3.12, а проект фиксирует Python 3.13
(`requires-python`), поэтому в `Dockerfile` Python 3.13 ставится сверху из PPA
`deadsnakes`, после чего Poetry ставит **основную** группу зависимостей проекта
(`poetry install --only main --no-root`). Dev-инструменты (ruff, mypy, pre-commit)
в образ не попадают. Команда по умолчанию — `pytest`.

### Запуск

```bash
# сборка образов и прогон всего набора; код возврата берётся от сервиса `tests`
docker compose up --build --exit-code-from tests

# если образы уже собраны — сборку можно не форсировать
docker compose up --exit-code-from tests
```

`--exit-code-from tests` заставляет Compose завершить работу и вернуть код выхода
сервиса `tests`, поэтому команда годится для CI. По окончании прогона все
контейнеры останавливаются, а БД удаляется.

Артефакты прогона сохраняются на хосте через тома, поэтому их можно посмотреть и
после остановки контейнеров:

```bash
# Allure-результаты из контейнера -> HTML-отчёт (см. Reporting)
allure generate allure-results -o allure-report --clean
```

- `./allure-results` — результаты Allure (`pytest.ini` пишет их туда же, что и локально);
- `./logs` — логи фреймворка (`logs/framework.log`).

### Полезные команды

```bash
# пересобрать образ тестов после изменения зависимостей
docker compose build tests

# разовый прогон отдельного набора/файла
docker compose run --rm tests pytest tests/api

# отключить сервис `webapp`, если приложение уже запущено на хосте
# (тогда задайте BASE_URL=http://host.docker.internal:8000)
docker compose run --rm -e BASE_URL=http://host.docker.internal:8000 tests pytest tests/api
```

Приложение-мишень собирается из Git-URL. Если приложение разрабатывается локально,
замените контекст сборки сервиса `webapp` на путь к его каталогу:

```yaml
    build:
      context: ../subscription-service-app
      dockerfile: Dockerfile
```

Примечания:

- контейнер `tests` запускается от **пользователя хоста** (`uid/gid`, по умолчанию
  `1000:1000`) — так артефакты на смонтированных томах остаются доступными
  локальному пользователю. При другом `uid/gid` задайте `DOCKER_UID`/`DOCKER_GID`
  (см. `user:` в `docker-compose.yml`); Chromium в образе работает и не от root;
- сервису `tests` включены `ipc: host` (Chromium требует общий раздел памяти) и
  `init: true` (reaper процессов против зомби-процессов);
- `.env` в контекст сборки не попадает (секреты), но образ создаёт `.env` в корне
  проекта (`/tests/.env`) из `.env.example`: фактические `BASE_URL`/`DB_URL` приходят
  переменными окружения Compose, которые в `pydantic-settings` имеют приоритет над `.env`;
- в образ ставится только **основная** группа зависимостей. `pytest-xdist`
  объявлен в основной группе (а не dev): сессионные фикстуры фреймворка
  (`run_manifest`, `_configure_logging`) используют фикстуру `worker_id`, которую
  предоставляет именно этот плагин, — без него тестовый набор не запускается.
