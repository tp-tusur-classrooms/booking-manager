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

## Создание учётных записей

Администратор создаётся через CLI после настройки БД и применения миграций:

```sh
uv run --frozen python -m scripts.create_admin --login admin --name "Администратор"
```

Пароль вводится скрыто дважды и сохраняется в виде bcrypt-хеша. Занятый логин
не изменяет существующий аккаунт. Для другого каталога настроек используйте
`--config-dir`. Логин содержит от 3 до 32 латинских букв, цифр, `.`, `_`, `-`;
регистр не учитывается. Имя содержит от 1 до 50 букв, пробелов и дефисов.
Пароль содержит от 8 до 16 символов: латиницу, цифры и `!#$%&*+-.<=>?@^_`.

После входа администратор создаёт пользователей запросом `POST /api/v1/users`
с заголовком `Authorization: Bearer <token>` и JSON:

```json
{
  "name": "Иван Иванов",
  "login": "ivanov",
  "password": "Secret-123",
  "confirm_password": "Secret-123"
}
```

Ответ `201` содержит созданного пользователя без пароля и токенов. Роль всегда
`user`, дополнительные поля запроса игнорируются. Новый пользователь затем
входит самостоятельно через `/auth/login`. Сессия администратора не меняется.
Без авторизации возвращается `401`, обычному пользователю `403`, при ошибках
полей `400`, при занятом логине `409 login_taken`. Публичной регистрации нет.

## Контракт API

[docs/openapi.yaml](docs/openapi.yaml) — статический контракт OpenAPI 3.1
для функций первого спринта: вход и выход, текущий пользователь
и роли, справочники, каталог и карточка аудитории, создание аудитории
с немедленной видимостью в каталоге, загрузка фотографии и учебное расписание.
По нему фронтенд и бэкенд разрабатываются параллельно. Правила авторизации,
истечения сессии, формат дат,
часовой пояс и формат ошибок описаны в начале файла.

Контракт открывается без запуска приложения. В браузере откройте
<https://editor.swagger.io> и выберите File → Import file. Либо запустите
Swagger UI в Docker из корня репозитория и откройте <http://localhost:8081>:

```sh
docker run --rm -p 8081:8080 -e SWAGGER_JSON=/spec/openapi.yaml -v "$(pwd)/docs:/spec" swaggerapi/swagger-ui
```

Валидность контракта и соответствие примеров схемам проверяет
`tests/test_openapi.py`.

## Аудитории: US-02, US-03, US-15

В миграциях `0001`–`0003` уже есть пользователи, роли и метаданные файлов.
Миграция `0004` добавляет только корпуса, оборудование, аудитории и связи
аудиторий с оборудованием. Фото использует существующую таблицу `file`.
Нужен PostgreSQL 18, как в Compose: Unicode-сравнение номеров в индексе
`uq_room_building_number` не зависит от локали базы, в том числе для кириллицы.

Соответствие формы `frontend/src/modules/classrooms/create.tsx` и API:

| Поле экрана | Создание | Хранение и чтение |
| --- | --- | --- |
| Номер | `number`, 1–20 символов, пробелы по краям убираются | `room.number`, уникален без учёта регистра внутри корпуса |
| Корпус | `building_id` из `/buildings` | `building: {id, name}` |
| Этаж | `floor`, целое от −5 до 50 | `room.floor` |
| Вместимость | `capacity`, целое от 1 до 1000 | `room.capacity` |
| Оборудование | `equipment_ids` из `/equipment`, по умолчанию `[]` | `room_equipment`, ответ `equipment: [{id, name}]` |
| Описание | `description`, до 1000 символов или `null` | `room.description` |
| Фото | Необязательный `file` в отдельном multipart-запросе | `room.photo_id` → `file`, ответ `photo_url` или `null` |

Все пути ниже имеют префикс `/api/v1` и требуют Bearer-токен:

- `GET /buildings`, `GET /equipment` — справочники по названию, `{items: []}`,
  если записей нет. Изменение справочников через HTTP не предусмотрено.
- `POST /rooms` — только администратор, JSON с полями формы. Ответ `201`
  содержит полную карточку с `id` и `status: published`. Она сразу доступна
  в управлении, каталоге (`GET /rooms`) и карточке (`GET /rooms/{id}`).
- `PUT /rooms/{id}/photo` — только администратор, поле `file`: JPG/PNG
  по содержимому, до 10 × 1024 × 1024 байт включительно. Ответ — полная
  карточка с абсолютным `photo_url`, доступным браузеру через `/public`.
  Новое фото заменяет старое; ошибка не меняет прежнее фото и не удаляет
  уже созданную аудиторию. Фронт повторяет загрузку без повторного создания.
- `POST /rooms/{id}/publish` — устаревший совместимый метод: возвращает
  уже опубликованную аудиторию без изменений. Новый фронтенд его не вызывает.

Ошибки различимы по HTTP-статусу и `code`: `400 validation_error` с полями
`errors`, `401` без входа, `403` при недостатке прав,
`404 not_found`, `409 room_number_taken`, `413 file_too_large`,
`415 unsupported_media_type`. Одинаковые номера в разных корпусах разрешены;
одновременные дубли в одном корпусе блокирует уникальный индекс БД.

Справочники наполняются вне API. Например, для **локальной демонстрации**
после миграций (повторное выполнение не создаёт дубли):

```sh
docker compose exec -T postgres psql -U booking_manager -d booking_manager <<'SQL'
INSERT INTO building (id, name) VALUES
  (gen_random_uuid(), 'Корпус 1'), (gen_random_uuid(), 'Корпус 2')
ON CONFLICT (name) DO NOTHING;
INSERT INTO equipment (id, name) VALUES
  (gen_random_uuid(), 'Интерактивная доска'), (gen_random_uuid(), 'Компьютеры'),
  (gen_random_uuid(), 'Микрофон'), (gen_random_uuid(), 'Проектор')
ON CONFLICT (name) DO NOTHING;
SQL
```

## Проверки

```sh
uv sync --locked --dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m unittest discover -s tests -v
```

Модульные тесты не требуют PostgreSQL или рабочих секретов. Интеграционные
тесты `tests/test_rooms_postgres.py` включаются через `ROOM_TEST_DATABASE_URL`
и создают отдельную случайную схему для каждого теста, применяют настоящие
миграции и удаляют только эту схему. Используйте локальную тестовую БД,
учётной записи нужны права `CREATE SCHEMA`:

```sh
ROOM_TEST_DATABASE_URL=postgresql+asyncpg://booking_manager:booking_manager_local@127.0.0.1:5432/booking_manager \
  uv run --frozen python -m unittest discover -s tests -v
```

Проверяются вход с JWT и права, немедленное чтение после создания, дубли
номеров (включая кириллицу и одновременные запросы), справочники, валидация,
фотографии и их замена/откат, миграция вниз/вверх и соответствие моделей БД.
CI поднимает PostgreSQL 18 и всегда выполняет интеграционные тесты.
Ветки, правила слияния и CI описаны в
[CONTRIBUTING.md](CONTRIBUTING.md).
