"""Настройка логирования тестового фреймворка на базе `loguru`.

Модуль предоставляет единую точку конфигурации логгера:

- :func:`setup_logging` — идемпотентная настройка sink'ов: цветной вывод в `stdout`
  и запись в файл ``logs/framework.log`` с ротацией, сжатием и удалением старых файлов;
- :func:`log_file_for_worker` — выбор лог-файла под конкретный процесс
  `pytest-xdist` (изоляция записи между воркерами);
- :func:`log_context` — контекстный менеджер для привязки метаданных
  (ID пользователя, ID заказа и т.п.) ко всем логам внутри блока.

Пример использования::

    from utils.logger import log_context, logger, setup_logging

    setup_logging()
    logger.info("Старт теста")

    with log_context(user_id=42, booking_id="bk-1"):
        logger.info("Бронирование создано")
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from config.settings import PROJECT_ROOT

if TYPE_CHECKING:
    from collections.abc import Iterator

    from loguru import Message, Record

__all__ = ["LOG_FILE", "LOGS_DIR", "log_context", "log_file_for_worker", "logger", "setup_logging"]

#: Каталог с лог-файлами фреймворка (исключён из Git в `.gitignore`).
LOGS_DIR: Path = PROJECT_ROOT / "logs"
#: Основной файл логов фреймворка (однопроцессный запуск).
LOG_FILE: Path = LOGS_DIR / "framework.log"

#: Идентификатор управляющего процесса `pytest-xdist` (вне распределённого запуска).
_MASTER_WORKER_ID = "master"


def log_file_for_worker(worker_id: str | None) -> Path:
    """Вернуть путь к лог-файлу для конкретного процесса `pytest-xdist`.

    При обычном (однопроцессном) запуске, а также для управляющего процесса
    (`master`) используется общий :data:`LOG_FILE`. В распределённом режиме
    каждый воркер (`gw0`, `gw1`, …) пишет в собственный файл
    ``logs/framework-<worker_id>.log`` — это исключает одновременную запись и
    ротацию одного и того же файла несколькими процессами (Race Conditions).

    Args:
        worker_id: Идентификатор воркера из фикстуры `worker_id` (`pytest-xdist`)
            или ``None``/``"master"`` для нераспределённого запуска.

    Returns:
        Path: Путь к лог-файлу соответствующего процесса.
    """
    if not worker_id or worker_id == _MASTER_WORKER_ID:
        return LOG_FILE
    return LOGS_DIR / f"framework-{worker_id}.log"


#: Ключ в `extra` записи, под которым :func:`log_context` хранит метаданные.
_CONTEXT_KEY = "context"

#: Значения `extra` по умолчанию — чтобы формат не падал без вызова `log_context`.
_DEFAULT_EXTRA: dict[str, Any] = {_CONTEXT_KEY: ""}

#: Флаг идемпотентности: повторный вызов :func:`setup_logging` не дублирует sink'и.
_configured = False


def _format_record(record: Record) -> str:
    """Динамический формат `loguru`: добавляет цветной контекст, если он задан.

    Loguru вызывает эту функцию для каждой записи, а возвращённая строка
    используется как шаблон формата. Поэтому символ перевода строки и
    ``{exception}`` добавляются здесь вручную (для динамических форматов
    loguru не делает это автоматически).
    """
    context_suffix = (
        f" | <yellow>{{extra[{_CONTEXT_KEY}]}}</yellow>"
        if record["extra"].get(_CONTEXT_KEY)
        else ""
    )
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        f"{context_suffix} | "
        "<level>{message}</level>\n{exception}"
    )


def _stdout_sink(message: Message) -> None:
    """Записать отформатированное сообщение в текущий `sys.stdout`.

    `sys.stdout` разрешается в момент записи (а не при `logger.add`), чтобы
    sink корректно работал при подмене потока средствами Pytest (`capsys`).
    """
    sys.stdout.write(message)


def setup_logging(
    *,
    worker_id: str | None = None,
    level: str = "DEBUG",
    rotation: str = "10 MB",
    retention: str = "10 days",
) -> None:
    """Настроить глобальные sink'и логгера (идемпотентно).

    Удаляет sink по умолчанию и добавляет два обработчика:

    - цветной вывод в `stdout` (уровень ``level``);
    - файловый sink (см. :func:`log_file_for_worker`) с ротацией ``rotation``,
      удалением старых файлов ``retention`` и сжатием в ``zip``.

    При повторном вызове настройка не дублируется (флаг ``_configured``).

    Args:
        worker_id: Идентификатор воркера `pytest-xdist`; под распределённым
            запуском переключает файловый sink на отдельный лог каждого процесса.
        level: Минимальный уровень логирования для обоих sink'ов.
        rotation: Условие ротации файла логов (размер или время).
        retention: Срок хранения старых лог-файлов до удаления.
    """
    global _configured

    if _configured:
        return

    log_file = log_file_for_worker(worker_id)

    logger.remove()
    logger.configure(extra=dict(_DEFAULT_EXTRA))

    logger.add(
        sink=_stdout_sink,
        level=level,
        format=_format_record,
        colorize=True,
        backtrace=True,
        diagnose=False,
    )
    logger.add(
        sink=log_file,
        level=level,
        format=_format_record,
        colorize=False,
        encoding="utf-8",
        rotation=rotation,
        retention=retention,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    _configured = True


@contextmanager
def log_context(**context: Any) -> Iterator[None]:
    """Привязать метаданные к логам внутри блока (`logger.contextualize`).

    Значения выводятся в отдельной секции формата и удобны для трассировки
    сущностей (ID пользователя, ID заказа и т.п.) в рамках одного сценария.

    Args:
        **context: Произвольные пары «ключ=значение» для логирования.

    Yields:
        None: управление передаётся телу блока ``with``.
    """
    formatted_context = " ".join(f"{key}={value}" for key, value in context.items())

    with logger.contextualize(**{_CONTEXT_KEY: formatted_context}):
        yield
