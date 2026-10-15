"""Check/Verify для M1.1: настройка логирования (`loguru`)."""

from __future__ import annotations

from uuid import uuid4

import allure
import pytest
from loguru import logger

from utils.logger import log_context, log_file_for_worker, setup_logging

pytestmark = pytest.mark.regression


@allure.feature("Observability")
@allure.story("Logging")
@allure.title("Log file is created and written")
def test_log_file_is_created_and_written(worker_id: str) -> None:
    """Файловый sink создаётся и получает сообщения без ANSI-кодов."""
    setup_logging()
    marker = f"log-file-marker-{uuid4()}"
    log_file = log_file_for_worker(worker_id)

    logger.info(marker)
    logger.complete()  # дождаться записи файлового sink (enqueue=True)

    assert log_file.is_file(), f"Лог-файл не создан: {log_file}"

    content = log_file.read_text(encoding="utf-8")

    assert marker in content, "Сообщение не попало в лог-файл"
    assert "\x1b[" not in content, "В лог-файле не должно быть ANSI-кодов цвета"


@allure.feature("Observability")
@allure.story("Logging")
@allure.title("setup_logging is idempotent")
def test_setup_logging_is_idempotent(worker_id: str) -> None:
    """Повторный вызов `setup_logging()` не дублирует sink'и."""
    setup_logging()
    setup_logging()
    marker = f"idempotency-marker-{uuid4()}"
    log_file = log_file_for_worker(worker_id)

    logger.info(marker)
    logger.complete()

    content = log_file.read_text(encoding="utf-8")

    assert content.count(marker) == 1, "Сообщение записано более одного раза — sink дублируется"


@allure.feature("Observability")
@allure.story("Logging")
@allure.title("log_context adds metadata to output")
def test_log_context_adds_metadata_to_output() -> None:
    """`log_context` добавляет метаданные во все логи внутри блока."""
    setup_logging()
    captured: list[str] = []

    def _collect(message: str) -> None:
        captured.append(message.rstrip("\n"))

    handler_id = logger.add(_collect, level="DEBUG", format="{message} | {extra[context]}")

    try:
        with log_context(user_id=42, booking_id="bk-1"):
            logger.info("booking created")
    finally:
        logger.remove(handler_id)

    assert captured == ["booking created | user_id=42 booking_id=bk-1"]


@allure.feature("Observability")
@allure.story("Logging")
@allure.title("log_context is not leaked outside the block")
def test_log_context_is_not_leaked_outside_block() -> None:
    """Вне блока `log_context` контекст не сохраняется."""
    setup_logging()
    captured: list[str] = []

    def _collect(message: str) -> None:
        captured.append(message.rstrip("\n"))

    handler_id = logger.add(_collect, level="DEBUG", format="{message} | {extra[context]}")

    try:
        with log_context(user_id=7):
            logger.info("inside")
        logger.info("outside")
    finally:
        logger.remove(handler_id)

    assert captured == ["inside | user_id=7", "outside | "]
