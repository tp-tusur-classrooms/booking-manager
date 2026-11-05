from pathlib import Path
from typing import Self

from fastapi import FastAPI

from src.low.app import App
from src.low.config.reader import ConfigReader
from src.low.creds.reader import CredsReader
from src.low.logging import initialize_logging


class BookingManager:
    """
    Инициализирует и управляет всеми низкоуровневыми компонентами приложения.

    Ответственность:
    - Загрузка конфигурации из config/prod/
    - Инициализация логирования
    - Создание и конфигурирование FastAPI приложения
    - Управление жизненным циклом приложения (lifespan)
    - Запуск uvicorn сервера
    """

    def __init__(self: Self, config_path: Path) -> None:
        # Запускаем сервер
        # 1. Грузим конфиг
        self.config_path = config_path

        self.load_configs()

        # 2. Инициализируем логгер
        self.create_logger()

        # 3. Создаем FastAPI приложение
        self.create_app()

    def get_config_paths(self: Self) -> tuple[Path, Path]:
        """Получить пути к файлам конфигурации и учетных данных."""
        return (
            self.config_path / Path("config.json"),
            self.config_path / Path("creds.json"),
        )

    def load_configs(self: Self) -> None:
        """Загрузить конфигурацию и учетные данные из JSON файлов."""
        cfg, cr = self.get_config_paths()
        self.config = ConfigReader.load(cfg)
        cr = self.config_path / self.config.general.creds
        self.creds = CredsReader.load(cr)

    def create_logger(self: Self) -> None:
        """Инициализировать логгеры для всех компонентов приложения."""
        initialize_logging(self.config.logging)

    def create_app(self) -> None:
        """Создать и сконфигурировать FastAPI приложение"""

        self.app = App(self.config, self.creds)
        self.app.create_app()


def create_app() -> FastAPI:
    """ASGI factory: uv run uvicorn main:create_app --factory."""
    return BookingManager(Path("config/prod")).app.app


if __name__ == "__main__":
    booking_manager = BookingManager(Path("config/prod"))
    booking_manager.app.start_uvicorn()
