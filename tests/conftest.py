"""Глобальные фикстуры Pytest: логирование, изоляция процессов и Allure.

Модуль решает три задачи:

- один раз за сессию включает sink'и `loguru` (:func:`utils.logger.setup_logging`),
  причём под `pytest-xdist` каждый процесс пишет в собственный лог-файл
  (см. :func:`utils.logger.log_file_for_worker`) — изоляция процессов;
- ведёт общий для всех воркеров манифест запуска (``logs/run.json``) под
  `filelock.FileLock` — защита общего файла от гонок (Race Conditions);
- для каждого теста перехватывает логи `loguru` и прикрепляет их к отчёту Allure.

`allure-pytest` подключается в отдельном майлстоуне; пока он не установлен,
прикрепление логов молча пропускается (см. :func:`_attach_logs_to_allure`).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import pytest
from filelock import FileLock
from loguru import logger

from utils.logger import LOGS_DIR, setup_logging

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from loguru import Message

#: Формат логов, прикрепляемых к отчёту (без цвета и служебных полей loguru).
_ATTACH_LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"

#: Манифест текущего запуска — общий артефакт всех воркеров `pytest-xdist`.
RUN_MANIFEST_FILE: Path = LOGS_DIR / "run.json"


def _current_run_id() -> str:
    """Идентификатор текущего запуска, общий для всех воркеров `pytest-xdist`.

    `pytest-xdist` публикует уникальный на запуск ``PYTEST_XDIST_TESTRUNUID``
    во всех воркерах; при обычном (однопроцессном) запуске переменной нет и
    используется константа ``local``.
    """
    return os.environ.get("PYTEST_XDIST_TESTRUNUID", "local")


def _read_run_manifest() -> dict[str, Any]:
    """Прочитать манифест запуска (пустой словарь, если файла ещё нет)."""
    if not RUN_MANIFEST_FILE.is_file():
        return {}
    try:
        data = json.loads(RUN_MANIFEST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


@pytest.fixture(scope="session")
def run_manifest(worker_id: str) -> dict[str, Any]:
    """Общий манифест запуска, обновляемый воркерами под `FileLock`.

    Под `pytest-xdist` несколько процессов одновременно стартуют сессию, и цикл
    «прочитать → изменить → записать» одного файла превращается в гонку
    (Race Conditions): без блокировки воркеры затирают обновления друг друга.
    `filelock.FileLock` сериализует доступ — файл остаётся консистентным, а все
    воркеры попадают в список ``workers``.

    Манифест содержит идентификатор и время старта запуска и список участвующих
    процессов; при смене запуска (по ``PYTEST_XDIST_TESTRUNUID``) он обнуляется,
    поэтому отражает только текущую сессию.
    """
    run_id = _current_run_id()
    RUN_MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(f"{RUN_MANIFEST_FILE}.lock")

    with lock:
        manifest = _read_run_manifest()
        if manifest.get("run_id") != run_id:
            manifest = {
                "run_id": run_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "workers": [],
            }
        workers = {str(worker) for worker in manifest.get("workers", [])}
        workers.add(worker_id)
        manifest["workers"] = sorted(workers)
        RUN_MANIFEST_FILE.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return manifest


@pytest.fixture(scope="session", autouse=True)
def _configure_logging(run_manifest: dict[str, Any], worker_id: str) -> None:
    """Один раз за сессию настроить sink'и `loguru` (stdout + файл с ротацией).

    Под `pytest-xdist` файловый sink ведёт ``log_file_for_worker`` — каждый
    воркер пишет в отдельный файл, поэтому процессы не мешают друг другу.
    """
    setup_logging(worker_id=worker_id)


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
