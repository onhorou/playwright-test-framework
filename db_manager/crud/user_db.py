"""CRUD-операции над таблицей ``users``.

Репозиторий предоставляет создание, чтение и удаление пользователей, а также
вспомогательные счётчики. Возвращает валидированные Pydantic-схемы
:class:`models.db.user.User`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.db import User

if TYPE_CHECKING:
    from db_manager.db_client import DBClient

__all__ = ["UserDB"]


class UserDB:
    """Репозиторий таблицы ``users`` поверх :class:`db_manager.db_client.DBClient`."""

    def __init__(self, client: DBClient) -> None:
        self._client = client

    def create(self, *, email: str, full_name: str) -> User:
        """Вставить пользователя и вернуть созданную строку."""
        row = self._client.fetch_one(
            "INSERT INTO users (email, full_name) VALUES (%s, %s) "
            "RETURNING id, email, full_name, created_at",
            (email, full_name),
        )
        if row is None:
            raise RuntimeError("INSERT ... RETURNING не вернул строку пользователя.")
        return User.model_validate(row)

    def get_by_email(self, email: str) -> User | None:
        """Вернуть пользователя по email или ``None``, если его нет."""
        row = self._client.fetch_one(
            "SELECT id, email, full_name, created_at FROM users WHERE email = %s",
            (email,),
        )
        return User.model_validate(row) if row is not None else None

    def get_by_id(self, user_id: int) -> User | None:
        """Вернуть пользователя по первичному ключу или ``None``."""
        row = self._client.fetch_one(
            "SELECT id, email, full_name, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        return User.model_validate(row) if row is not None else None

    def count(self) -> int:
        """Вернуть общее число записей в таблице ``users``."""
        row = self._client.fetch_one("SELECT count(*) AS count FROM users")
        return int(row["count"]) if row is not None else 0

    def delete_by_email(self, email: str) -> int:
        """Удалить пользователя по email; вернуть число удалённых строк."""
        return self._client.execute("DELETE FROM users WHERE email = %s", (email,))

    def delete_by_id(self, user_id: int) -> int:
        """Удалить пользователя по первичному ключу; вернуть число удалённых строк."""
        return self._client.execute("DELETE FROM users WHERE id = %s", (user_id,))
