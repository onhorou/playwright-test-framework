# playwright-test-framework

Test automation framework for the **subscription-service-app** (API + UI + DB),
built with **Playwright**, **Pytest** and **Poetry**.

## Stack

- **Python 3.13** (pinned in `.python-version`)
- **Poetry** 2.x — dependency and environment management
- **Pytest** + **pytest-playwright** — test runner and Playwright fixtures
- **Pydantic v2** + **pydantic-settings** — DTOs and configuration
- **Loguru** — logging

## Requirements

- Python 3.13
- Poetry 2.x

## Setup

```bash
# create (or reuse) the virtualenv with Python 3.13 and install dependencies
poetry env use python3.13
poetry install
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

## Run tests

```bash
poetry run pytest
```
