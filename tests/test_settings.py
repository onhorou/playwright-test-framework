"""Check/Verify для M1: корректность загрузки настроек из `.env`."""

import allure

from config.settings import ENV_FILE, Settings, get_settings


@allure.feature("Framework configuration")
@allure.story("Settings")
@allure.title("The .env file exists in the project root")
def test_env_file_exists() -> None:
    """Файл `.env` присутствует в корне проекта."""
    assert ENV_FILE.is_file(), f"Не найден файл окружения: {ENV_FILE}"


@allure.feature("Framework configuration")
@allure.story("Settings")
@allure.title("get_settings returns a cached singleton")
def test_get_settings_returns_cached_singleton() -> None:
    """`get_settings()` возвращает один и тот же экземпляр (lru_cache)."""
    assert get_settings() is get_settings()


@allure.feature("Framework configuration")
@allure.story("Settings")
@allure.title("Required variables are loaded from .env")
def test_settings_are_loaded_from_env() -> None:
    """Обязательные переменные успешно прочитаны из окружения."""
    settings = Settings()

    assert settings.base_url.startswith("http"), settings.base_url
    assert settings.db_url, "DB_URL не должен быть пустым"


@allure.feature("Framework configuration")
@allure.story("Settings")
@allure.title("DB_URL looks like a PostgreSQL DSN")
def test_db_url_looks_like_postgres_dsn() -> None:
    """`DB_URL` имеет ожидаемый вид DSN для PostgreSQL."""
    assert Settings().db_url.startswith(("postgresql://", "postgres://"))
