# Управление бронированием аудиторий

Сервис бронирования аудиторий ТУСУР. Бэкенд: Python 3.13, FastAPI,
SQLAlchemy и PostgreSQL. Фронтенд: React, TypeScript, Vite и Tailwind CSS.

## Структура репозитория

```text
main.py                ASGI-фабрика и запуск бэкенда
src/api/               HTTP API
src/domain/            Модели, схемы, сервисы и репозитории
src/low/               Конфигурация, DI, БД, middleware и логирование
alembic/               Миграции PostgreSQL
docs/openapi.yaml      Контракт API первого спринта
config/example/        Примеры настроек без рабочих секретов
scripts/               Подготовка локального окружения и проверка PR
tests/                 Автоматические тесты бэкенда и правил PR
.github/               CI и шаблон pull request
frontend/              Пользовательские и административные страницы
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

Для запуска фронтенда установите закреплённые версии Node.js и npm. Из
каталога `frontend/` запустите `npm ci` и `npm run dev`, затем откройте
<http://localhost:5000>. Настройки связи с API и запуск production-сборки
описаны в [README фронтенда](frontend/README.md).

## Контракт API

[docs/openapi.yaml](docs/openapi.yaml) — статический контракт OpenAPI 3.1
для функций первого спринта: регистрация, вход и выход, текущий пользователь
и роли, справочники, каталог и карточка аудитории, создание и публикация
аудитории, загрузка фотографии и учебное расписание. По нему фронтенд и бэкенд
разрабатываются параллельно. Правила авторизации, истечения сессии, формат дат,
часовой пояс и формат ошибок описаны в начале файла.

Контракт открывается без запуска приложения. В браузере откройте
<https://editor.swagger.io> и выберите File → Import file. Либо запустите
Swagger UI в Docker из корня репозитория и откройте <http://localhost:8081>:

```sh
docker run --rm -p 8081:8080 -e SWAGGER_JSON=/spec/openapi.yaml -v "$(pwd)/docs:/spec" swaggerapi/swagger-ui
```

Валидность контракта и соответствие примеров схемам проверяет
`tests/test_openapi.py`.

## Проверки

```sh
uv sync --locked --dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m unittest discover -s tests -v
```

Тесты не требуют PostgreSQL, SMTP или рабочих секретов.
Ветки, правила слияния и CI описаны в
[CONTRIBUTING.md](CONTRIBUTING.md).
