from collections.abc import AsyncGenerator
import logging
from pathlib import Path
from typing import Any, Self

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse
import uvicorn

from src.api.v1.router import api_router
from src.low.config.reader import ConfigReader
from src.low.container import container, setup_container
from src.low.creds.reader import CredsReader
from src.low.exceptions import UserException
from src.low.logging import logger
from src.low.middleware import (
    DatabaseSessionMiddleware,
    ErrorHandlingMiddleware,
    MetricsMiddleware,
    TimeoutMiddleware,
)


class App:
    """
    Класс обертка вокруг создания и настройки приложения в FastAPI
    """

    def __init__(self: Self, config: ConfigReader, creds: CredsReader) -> None:
        self.config = config
        self.creds = creds

    def create_app(self: Self) -> None:

        # 1. Создаем экземляр приложения
        self.app = FastAPI(
            title=self.config.settings.PROJECT_NAME,
            version=self.config.settings.VERSION,
            lifespan=self.lifespan,
            # Сохраняем JWT в сваггера между перезагрузками
            swagger_ui_parameters={"persistAuthorization": True},
        )

        # 1.5 Регистрируем обработчик для ошибок валидации Pydantic
        @self.app.exception_handler(RequestValidationError)
        async def validation_error_handler(
            request: Any, exc: RequestValidationError
        ) -> JSONResponse:
            message = ""
            try:
                message = exc._errors[0]["msg"]
            except Exception:
                message = "Parsing error"
            user_error = UserException(message=str(message), status_code=400)
            return JSONResponse(
                status_code=user_error.status_code,
                content=user_error.to_api().model_dump(),
            )

        # 2. Конфигурируем FastApi middleware
        self._configure_middlewares()

        # 3. Собираем все роутеры
        # Это важно сделать до генерации (в FastAPI - lazy) openapi
        # Чтобы все роуты там отобразились
        self._register_routers()

        # 4. Монтируем статические файлы
        self._mount_static_files()

        # 5. Различные конфигурации для swagger
        self._setup_openapi()

    def _setup_openapi(self: Self) -> None:
        """
        Вся конфигурация по swagger
        """

        # Генерируем схему по уже заданным параметрам
        # Это включает все уже заданные роуты из роутеров, вебхуки и прочее
        # А также множество другой "документации"
        openapi_schema: dict[str, Any] = self.app.openapi()

        # Задаем теги (разделы)
        openapi_schema["tags"] = [
            {
                "name": "Auth",
                "description": "Авторизация",
            },
            {
                "name": "Users",
                "description": "Профили пользователей",
            },
        ]

        # Включаем BearerAuth (JWT) на securitySchemes
        openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
        openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

        self.app.openapi_schema = openapi_schema

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None]:
        """
        ЖЦ FastAPI приложения

        Startup:
        - Инициализация базы данных
        - Конфигурирование DI контейнера

        Shutdown:
        - Закрытие соединений с БД
        """
        # 1. Регистрируем логгер для ЖЦ
        lifespan_logger = logger.register_logger(
            "BookingManager.lifespan", level=logging.INFO
        )

        # 2. Подключаемся к БД и сохраняем инстанс в app.state для передачи в обвязку
        # 3. Создание обвязки - реализована через контейнер dependency-injection
        await setup_container(self.config.modules, self.creds.modules)
        app.state.db = container.db()
        lifespan_logger.info("DI container initialized")

        try:
            # Фактически, при помощи @asynccontextmanager происходит запуск некого
            # FastAPI кода, который при выходе или ошибке рано или поздно попадет в этот
            # блок, тем самым выполнив graceful shutdown
            yield
        finally:
            # Приложение остановлено, производим graceful shutdown
            lifespan_logger.info("Shutting down")

            await app.state.db.close()
            container.unwire()
            container.reset_singletons()
            lifespan_logger.info("Milestone reached: Database connections closed")
            lifespan_logger.info("Milestone reached: Application shutdown complete")

    def _configure_middlewares(self: Self) -> None:
        """
        Настроить все HTTP middleware

        Порядок: FastAPI применяет add_middleware через insert(0), поэтому
        тот, что добавлен ПЕРВЫМ, в итоге обрабатывает запрос ПОСЛЕДНИМ
        (становится самым внутренним), а добавленный последним - самым
        внешним.
        """

        # Закрытие SQLAlchemy session после каждого запроса.
        # Добавляется ПЕРВЫМ, чтобы оказаться самым внутренним user
        # middleware - так pure ASGI код бежит в том же task'е, что и
        # обработчик, и ContextLocalSingleton.session доступен через
        # ContextVar. BaseHTTPMiddleware ниже (Timeout/Metrics/Error)
        # порождают дочерние task'и при call_next, поэтому видеть
        # ContextVar обработчика они не могут.
        self.app.add_middleware(DatabaseSessionMiddleware)

        # Корс по origin из конфига
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin).rstrip("/")
                for origin in self.config.networking.frontend.origin
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Кастомная обработка любых ошибок сервера
        self.app.add_middleware(ErrorHandlingMiddleware)  # type: ignore

        # Сбор и логирование метрик
        self.app.add_middleware(MetricsMiddleware)  # type: ignore

        # Таймауты на все
        self.app.add_middleware(TimeoutMiddleware, default_timeout=5.0)  # type: ignore

    def _register_routers(self: Self) -> None:
        """
        Подключить маршруты API

        роутеры создадутся в момент импорта модулей api
        на момент вызова поле registered_routers уже будет заполенено
        всеми роутерами
        """

        self.global_router = api_router

        self.app.include_router(
            self.global_router, prefix=self.config.settings.API_V1_STR
        )

    def _mount_static_files(self: Self) -> None:
        """Монтировать статические файлы для доступа через HTTP"""

        public_path = Path(self.config.modules.files.public_path)
        public_path.mkdir(parents=True, exist_ok=True)
        if public_path.exists():
            self.app.mount(
                "/public",
                StaticFiles(directory=str(public_path)),
                name="public",
            )
        else:
            logger.register_logger("App").warning(
                f"Public directory not found: {public_path}"
            )

    def start_uvicorn(self: Self) -> None:
        """Поднять uvicorn сервер"""

        uvicorn_logger = logger.register_logger("uvicorn")
        uvicorn_logger.info(
            f"Starting server on port {self.config.networking.server_port}"
        )

        # Конфиг логгинга для uvicorn
        # Нужет чтобы он не писал в консоль все сам, а в место этого
        # использовался только глобальный логгер
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {
                "uvicorn": {"handlers": [], "level": "INFO", "propagate": True},
                "uvicorn.error": {"handlers": [], "level": "INFO", "propagate": True},
                "uvicorn.access": {"handlers": [], "level": "INFO", "propagate": True},
            },
        }

        uvicorn.run(
            self.app,
            host=self.config.networking.server_host,
            port=self.config.networking.server_port,
            log_level=logging.DEBUG,
            log_config=logging_config,
        )
