# playwright-test-framework

Test automation framework for the **subscription-service-app** (API + UI + DB),
built with **Playwright**, **Pytest** and **Poetry**.

## Stack

- **Python 3.13** (pinned in `.python-version`)
- **Poetry** 2.x — dependency and environment management
- **Pytest** + **pytest-playwright** — test runner and Playwright fixtures
- **Pydantic v2** + **pydantic-settings** — DTOs and configuration

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

## Run tests

```bash
poetry run pytest
```
