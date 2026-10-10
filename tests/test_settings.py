"""Check/Verify для M1: корректность загрузки настроек из `.env`."""

from config.settings import ENV_FILE, Settings, get_settings


def test_env_file_exists() -> None:
    """Файл `.env` присутствует в корне проекта."""
    assert ENV_FILE.is_file(), f"Не найден файл окружения: {ENV_FILE}"


def test_get_settings_returns_cached_singleton() -> None:
    """`get_settings()` возвращает один и тот же экземпляр (lru_cache)."""
    assert get_settings() is get_settings()


def test_settings_are_loaded_from_env() -> None:
    """Обязательные переменные успешно прочитаны из окружения."""
    settings = Settings()

    assert settings.base_url.startswith("http"), settings.base_url
    assert settings.db_url, "DB_URL не должен быть пустым"


def test_db_url_looks_like_postgres_dsn() -> None:
    """`DB_URL` имеет ожидаемый вид DSN для PostgreSQL."""
    assert Settings().db_url.startswith(("postgresql://", "postgres://"))
