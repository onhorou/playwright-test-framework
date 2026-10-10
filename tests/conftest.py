"""Глобальные фикстуры Pytest и интеграция логирования с отчётами.

Модуль решает две задачи:

- один раз за сессию включает sink'и `loguru` (:func:`utils.logger.setup_logging`);
- для каждого теста перехватывает логи `loguru` и прикрепляет их к отчёту Allure.

`allure-pytest` подключается в отдельном майлстоуне; пока он не установлен,
прикрепление логов молча пропускается (см. :func:`_attach_logs_to_allure`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from loguru import logger

from utils.logger import setup_logging

if TYPE_CHECKING:
    from collections.abc import Iterator

    from loguru import Message

#: Формат логов, прикрепляемых к отчёту (без цвета и служебных полей loguru).
_ATTACH_LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"


@pytest.fixture(scope="session", autouse=True)
def _configure_logging() -> None:
    """Один раз за сессию настроить sink'и `loguru` (stdout + файл с ротацией)."""
    setup_logging()


def _attach_logs_to_allure(name: str, lines: list[str]) -> None:
    """Прикрепить перехваченные логи к отчёту Allure, если он доступен.

    Импорт `allure` выполняется «мягко»: пока пакет `allure-pytest` не установлен,
    функция ничего не делает.
    """
    if not lines:
        return

    try:
        import allure
    except ImportError:
        return

    allure.attach(
        "\n".join(lines),
        name=f"loguru logs — {name}",
        attachment_type=allure.attachment_type.TEXT,
    )


@pytest.fixture(autouse=True)
def _capture_logs(request: pytest.FixtureRequest) -> Iterator[None]:
    """Перехватить логи `loguru` текущего теста и приложить их к отчёту."""
    records: list[str] = []

    def _sink(message: Message) -> None:
        records.append(message.rstrip())

    handler_id = logger.add(_sink, level="DEBUG", format=_ATTACH_LOG_FORMAT)

    try:
        yield
    finally:
        logger.remove(handler_id)
        _attach_logs_to_allure(request.node.name, records)
