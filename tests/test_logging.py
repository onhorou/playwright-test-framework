"""Check/Verify для M1.1: настройка логирования (`loguru`)."""

from __future__ import annotations

from uuid import uuid4

from loguru import logger

from utils.logger import LOG_FILE, log_context, setup_logging


def test_log_file_is_created_and_written() -> None:
    """Файловый sink создаётся и получает сообщения без ANSI-кодов."""
    setup_logging()
    marker = f"log-file-marker-{uuid4()}"

    logger.info(marker)
    logger.complete()  # дождаться записи файлового sink (enqueue=True)

    assert LOG_FILE.is_file(), f"Лог-файл не создан: {LOG_FILE}"

    content = LOG_FILE.read_text(encoding="utf-8")

    assert marker in content, "Сообщение не попало в лог-файл"
    assert "\x1b[" not in content, "В лог-файле не должно быть ANSI-кодов цвета"


def test_setup_logging_is_idempotent() -> None:
    """Повторный вызов `setup_logging()` не дублирует sink'и."""
    setup_logging()
    setup_logging()
    marker = f"idempotency-marker-{uuid4()}"

    logger.info(marker)
    logger.complete()

    content = LOG_FILE.read_text(encoding="utf-8")

    assert content.count(marker) == 1, "Сообщение записано более одного раза — sink дублируется"


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
