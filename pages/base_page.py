"""Базовый класс страницы (Page Object Model) для UI-тестов.

:class:`BasePage` — тонкая обёртка над Playwright `Page`: она хранит ссылку
на страницу и предоставляет единообразные методы для навигации и работы с
элементами по значению атрибута `data-testid`. Конкретные страницы
(например, :class:`pages.home_page.HomePage`) наследуются от :class:`BasePage`
и описывают свои элементы и сценарии, а тесты вызывают бизнес-действия
страниц, не работая с селекторами напрямую.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

__all__ = ["BasePage"]


class BasePage:
    """Общие операции над страницей, переиспользуемые всеми Page Object'ами."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self, path: str = "/") -> None:
        """Открыть путь относительно `base_url` браузерного контекста.

        `base_url` задаётся в фикстурах (`tests/ui/conftest.py`) из настроек
        приложения, поэтому пути указываются относительными (например, ``"/"``).
        """
        self.page.goto(path)

    def by_testid(self, test_id: str) -> Locator:
        """Вернуть локатор элемента по значению атрибута `data-testid`."""
        return self.page.get_by_test_id(test_id)

    def click(self, test_id: str) -> None:
        """Кликнуть по элементу с указанным `data-testid`."""
        self.by_testid(test_id).click()

    def fill(self, test_id: str, value: str) -> None:
        """Заполнить поле с указанным `data-testid` значением `value`."""
        self.by_testid(test_id).fill(value)

    def text(self, test_id: str) -> str:
        """Вернуть текстовое содержимое элемента без обрамляющих пробелов."""
        return (self.by_testid(test_id).text_content() or "").strip()

    def attribute(self, test_id: str, name: str) -> str | None:
        """Вернуть значение атрибута `name` у элемента с указанным `data-testid`."""
        return self.by_testid(test_id).get_attribute(name)

    def is_visible(self, test_id: str) -> bool:
        """Проверить видимость элемента с указанным `data-testid`."""
        return self.by_testid(test_id).is_visible()

    def wait_for_visible(self, test_id: str) -> None:
        """Дождаться появления видимого элемента с указанным `data-testid`."""
        self.by_testid(test_id).wait_for(state="visible")
