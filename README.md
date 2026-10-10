# playwright-test-framework

Test automation framework for the **subscription-service-app** (API + UI + DB),
built with **Playwright**, **Pytest** and **Poetry**.

## Stack

- **Python 3.13** (pinned in `.python-version`)
- **Poetry** 2.x — dependency and environment management
- **Pytest** + **pytest-playwright** — test runner and Playwright fixtures
- **Pydantic v2** + **pydantic-settings** — DTOs and configuration

## Requirements

- Python 3.13
- Poetry 2.x

## Setup

```bash
# create (or reuse) the virtualenv with Python 3.13 and install dependencies
poetry env use python3.13
poetry install
```

## Run tests

```bash
poetry run pytest
```
