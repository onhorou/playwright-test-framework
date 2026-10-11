"""Базовый клиент подключения к PostgreSQL (`psycopg` 3) для DB-тестов.

:class:`DBClient` — тонкая обёртка над соединением `psycopg`: она выполняет
SQL-запросы и единообразно логирует их, ничего не зная о конкретных таблицах.
Строки результата возвращаются словарями (`dict_row`), что упрощает их
дальнейшую валидацию Pydantic-схемами из :mod:`models.db`.

Репозитории конкретных таблиц группируются в пакете :mod:`db_manager.crud`
и получают экземпляр :class:`DBClient` в конструктор — тот же принцип, что и
у :class:`api_manager.api_client.APIClient` в API-слое.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import psycopg
from psycopg.rows import dict_row

from utils.logger import logger

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import TracebackType

    from psycopg import Connection

__all__ = ["DBClient"]

#: Максимальная длина SQL-запроса в логе (длинные запросы обрезаются).
_LOG_QUERY_LIMIT = 120


def _shorten(query: str, limit: int = _LOG_QUERY_LIMIT) -> str:
    """Сжать SQL-запрос в одну строку и обрезать до ``limit`` символов."""
    flattened = " ".join(query.split())
    if len(flattened) <= limit:
        return flattened
    return f"{flattened[:limit]}…"


class DBClient:
    """Обёртка над соединением `psycopg` с единым логированием запросов."""

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._connection: Connection[dict[str, Any]] | None = None

    def connect(self) -> None:
        """Открыть соединение с БД (идемпотентно).

        ``autocommit=True`` — каждый оператор фиксируется сразу, что удобно для
        тестового окружения: чтения и зачистка данных не зависят от состояния
        незавершённой транзакции.
        """
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(
                self._db_url,
                row_factory=dict_row,
                autocommit=True,
            )

    def close(self) -> None:
        """Закрыть соединение, если оно было открыто."""
        if self._connection is not None and not self._connection.closed:
            self._connection.close()
        self._connection = None

    @property
    def connection(self) -> Connection[dict[str, Any]]:
        """Нижележащее соединение `psycopg` (должно быть открыто через :meth:`connect`)."""
        if self._connection is None or self._connection.closed:
            raise RuntimeError("Соединение с БД не открыто: вызовите DBClient.connect().")
        return self._connection

    def __enter__(self) -> DBClient:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def execute(
        self,
        query: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> int:
        """Выполнить запрос и вернуть количество затронутых строк (``rowcount``)."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            rowcount = cursor.rowcount
        logger.debug(
            "DB {query} -> {rowcount} row(s)",
            query=_shorten(query),
            rowcount=rowcount,
        )
        return rowcount

    def fetch_one(
        self,
        query: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Выполнить запрос и вернуть одну строку (или ``None``)."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
        logger.debug(
            "DB {query} -> {rows} row(s)",
            query=_shorten(query),
            rows=0 if row is None else 1,
        )
        return row

    def fetch_all(
        self,
        query: str,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Выполнить запрос и вернуть все строки результата."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = list(cursor.fetchall())
        logger.debug(
            "DB {query} -> {rows} row(s)",
            query=_shorten(query),
            rows=len(rows),
        )
        return rows
