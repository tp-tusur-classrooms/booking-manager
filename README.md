# Управление бронированием аудиторий

Сервис бронирования аудиторий ТУСУР. Бэкенд: Python 3.13, FastAPI,
SQLAlchemy и PostgreSQL. Фронтенд пока не добавлен.

## Структура репозитория

```text
main.py                ASGI-фабрика и запуск бэкенда
src/api/               HTTP API
src/domain/            Модели, схемы, сервисы и репозитории
src/low/               Конфигурация, DI, БД, middleware и логирование
alembic/               Миграции PostgreSQL
config/example/        Примеры настроек без рабочих секретов
scripts/               Подготовка локального окружения и проверка PR
tests/                 Автоматические тесты бэкенда и правил PR
.github/               CI и шаблон pull request
frontend/              Место будущего фронтенда (ещё не создано)
pyproject.toml, uv.lock Зависимости и их зафиксированные версии
docker-compose.yml     Локальный PostgreSQL
```

Существующий бэкенд остаётся в корне; перемещение в `backend/` не требуется.

## Локальный запуск

Установите Python 3.13, [uv](https://docs.astral.sh/uv/getting-started/installation/)
и Docker Compose. Из корня репозитория:

```sh
uv sync --locked --dev
uv run --frozen python scripts/configure.py
docker compose up -d postgres
uv run --frozen alembic upgrade head
uv run --frozen uvicorn main:create_app --factory --reload
```

На Linux для работы `python-magic` нужна системная библиотека `libmagic1`;
на Windows установите совместимую libmagic по инструкции python-magic.
Настройки создаются в `config/prod/`; повторный запуск не перезаписывает их.
Учётные данные из Compose предназначены только для локальной разработки.
Для рабочего окружения задайте собственные секреты вне Git.

## Проверки

```sh
uv sync --locked --dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m unittest discover -s tests -v
```

Тесты не требуют PostgreSQL, SMTP или рабочих секретов.
Ветки, правила слияния, CI и требования к будущему фронтенду описаны в
[CONTRIBUTING.md](CONTRIBUTING.md).
