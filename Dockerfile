# syntax=docker/dockerfile:1

# =============================================================================
# Образ тестового фреймворка (контейнер `tests`).
#
# База — официальный образ Playwright для Python, зафиксированный на ТОЙ ЖЕ
# версии Playwright, что и в `poetry.lock` (1.63.0). Образ уже содержит браузеры
# (chromium-1243, firefox-1543, webkit-2359) и их системные зависимости, поэтому
# тег нельзя обновлять отдельно от Python-зависимости: при рассинхроне версий
# Playwright не найдёт исполняемые файлы браузеров.
#
# В самом образе есть только Python 3.12, а проект фиксирует Python 3.13
# (`requires-python = ">=3.13,<4.0"`), поэтому Python 3.13 ставится сверху
# из PPA deadsnakes до установки зависимостей проекта.
# =============================================================================
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PATH="/tests/.venv/bin:/opt/poetry/bin:${PATH}"

# --- Python 3.13 (базовый образ содержит 3.12) -------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common gnupg \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3.13 python3.13-venv \
    && rm -rf /var/lib/apt/lists/*

# --- Poetry (в изолированном виртуальном окружении) --------------------------
RUN python3.13 -m venv "${POETRY_HOME}" \
    && "${POETRY_HOME}/bin/pip" install --no-cache-dir --upgrade pip \
    && "${POETRY_HOME}/bin/pip" install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /tests

# Runtime-зависимости ставим отдельным слоем (кэшируется, пока не изменились
# `pyproject.toml`/`poetry.lock`). Ставится только основная группа — всё, что
# нужно для запуска тестов; dev-инструменты (ruff, mypy, pre-commit) в образ
# не попадают.
COPY pyproject.toml poetry.lock ./
RUN poetry env use python3.13 \
    && poetry install --only main --no-root \
    && rm -rf "${POETRY_CACHE_DIR}"

# Исходники фреймворка (тесты, Page Object'ы, клиенты, модели, pytest.ini, ...).
COPY . .

# `.env` исключён из контекста сборки (`.dockerignore` — секреты не попадают в
# образ), но фреймворк ожидает файл настроек в корне проекта. Создаём его из
# шаблона: фактические значения приходят переменными окружения Compose, а те
# имеют приоритет над `.env` в `pydantic-settings`.
RUN cp .env.example .env

# Проектный каталог доступен для записи: контейнер запускается от произвольного
# uid (см. `user:` в `docker-compose.yml`), а pytest и Playwright пишут кэш и
# артефакты прогона в рабочий каталог.
RUN chmod -R a+rwX /tests

# По умолчанию — прогон всего набора. Переопределяется, например:
#   docker compose run --rm tests pytest tests/api
CMD ["pytest"]
