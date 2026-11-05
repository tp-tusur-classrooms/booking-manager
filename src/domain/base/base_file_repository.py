from pathlib import Path
from typing import BinaryIO, Self

import aiofiles
import aiofiles.os as aio_os

from src.low.exceptions import FileNotFoundException


class BaseFileRepository:
    """
    Базовый файл для любых файловых репозиториев

    Предоставляет базовый CR_D функционал. Работает в контексте подпапок
    """

    def __init__(self: Self, base_folder: Path) -> None:
        self._base_folder = Path(base_folder)
        self._base_folder.mkdir(parents=True, exist_ok=True)

    def _get_secure_path(self, sub_folder: str, file_name: str) -> Path:
        """
        Получить правльный путь, который никогда не выйдет за пределы _base_dir
        """
        target_dir = (self._base_folder / sub_folder).resolve()
        target_path = (target_dir / file_name).resolve()

        if not target_path.is_relative_to(self._base_folder.resolve()):
            raise FileNotFoundException()

        return target_path

    def get_clear_path(self: Self, sub_folder: str, file_name: str) -> Path:
        """
        Резолвит правильный безопасный путь до подпапки,
        создавая её, если это необходимо
        """

        clear_path = self._get_secure_path(sub_folder, file_name)
        clear_path.parent.mkdir(parents=False, exist_ok=True)

        return clear_path

    async def save(self, sub_folder: str, file_name: str, content: bytes) -> None:
        clear_path = self.get_clear_path(sub_folder, file_name)

        async with aiofiles.open(clear_path, "wb") as f:
            await f.write(content)

    async def save_stream(
        self, sub_folder: str, file_name: str, file_obj: BinaryIO
    ) -> int:
        clear_path = self.get_clear_path(sub_folder, file_name)

        size = 0
        chunk_size = 1024 * 1024

        async with aiofiles.open(clear_path, "wb") as f:
            while True:
                # Если file_obj это UploadFile, то read асинхронный, иначе не факт
                chunk = await file_obj.read(chunk_size)  # type: ignore
                if not chunk:
                    break
                await f.write(chunk)
                size += len(chunk)

        return size

    async def delete(self: Self, sub_folder: str, file_name: str) -> None:
        clear_path = self.get_clear_path(sub_folder, file_name)
        if clear_path.exists():
            await aio_os.remove(clear_path)

    async def get_path(self: Self, sub_folder: str, file_name: str) -> Path:
        clear_path = self.get_clear_path(sub_folder, file_name)
        if not clear_path.exists():
            raise FileNotFoundException()
        return clear_path

    async def exists(self, sub_folder: str, file_name: str) -> bool:
        return self.get_clear_path(sub_folder, file_name).exists()
