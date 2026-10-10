"""Настройки тестового фреймворка: чтение переменных окружения из `.env`.

Модуль построен на `pydantic-settings`: значения читаются из файла `.env`
в корне проекта и переопределяются переменными окружения процесса.
Единая точка доступа к настройкам — фабрика `get_settings()`,
кэширующая результат через `functools.lru_cache` (singleton).
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Корень проекта (директория, содержащая пакет `config/`).
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
#: Путь к файлу `.env` в корне проекта.
ENV_FILE: Path = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Настройки окружения, необходимые тестам фреймворка."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: str = Field(
        ...,
        description="Базовый URL тестируемого приложения, например http://localhost:8000.",
    )
    db_url: str = Field(
        ...,
        description=(
            "Строка подключения к базе данных, "
            "например postgresql://user:password@host:port/database."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Вернуть закэшированный экземпляр настроек (singleton).

    Значения читаются из `.env` в корне проекта при первом вызове
    и далее переиспользуются благодаря `functools.lru_cache`.
    """
    return Settings()
