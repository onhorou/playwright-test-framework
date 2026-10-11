"""Page Object Model (POM) для UI-тестов тестируемого приложения.

Пакет содержит базовый класс страницы (:class:`pages.base_page.BasePage`)
и Page Object'ы конкретных страниц/компонентов (например,
:class:`pages.home_page.HomePage`, :class:`pages.login_page.LoginPage` и
:class:`pages.dashboard_page.DashboardPage`).
Тесты оперируют бизнес-действиями страниц и не работают с селекторами напрямую.
"""
