from abc import ABC, abstractmethod
import asyncio
import io
from pathlib import Path
from typing import Self
import uuid

from fastapi import UploadFile
import magic
from PIL import Image, ImageOps, UnidentifiedImageError

from src.domain.base.base_service import BaseService
from src.domain.file.repositories import FileMetadataRepository, FileRepository
import src.domain.file.schemas as file_schema
from src.low.exceptions import (
    FileNotFoundException,
    ServerException,
    UnknownFileTypeException,
)


class BaseFileService(BaseService, ABC):
    def __init__(
        self: Self,
        public_url: str,
        file_repository: FileRepository,
        file_metadata_repository: FileMetadataRepository,
        sub_folder: str,
    ) -> None:
        self.public_url = public_url
        self.file_repository = file_repository
        self.file_metadata_repository = file_metadata_repository
        self.sub_folder = sub_folder

    @abstractmethod
    async def validate_file(self, file: UploadFile) -> None:
        pass

    async def save(
        self: Self, owner_user_id: uuid.UUID, file: UploadFile
    ) -> file_schema.FileMetadata:
        """Сохранить файл"""

        # валидация файла, может быть любой
        await self.validate_file(file)
        # Сбрасываем позицию чтения файла
        await file.seek(0)

        filename: str = file.filename or ""

        # Название файла: image.png -> 67affd52-82ba-45e9-a9fa-43ff1760a84epng
        ext = Path(filename).suffix
        stored_name = f"{uuid.uuid4().hex}{ext}"

        # Сохраняем файл
        size: int = await self._process_and_save(file, stored_name)

        metadata = file_schema.CreateFileMetadata(
            user_id=owner_user_id,
            sub_folder=self.sub_folder,
            original_filename=filename,
            stored_filename=stored_name,
            size=size,
        )

        # Сохраняем метадату о файле
        try:
            saved_metadata = await self.file_metadata_repository.create(metadata)
            return file_schema.FileMetadata.model_validate(
                saved_metadata, from_attributes=True
            )
        except Exception as e:
            # Если случилась ошибка при сохранении файла, удаляем сохраненный файл
            await self.file_repository.delete(self.sub_folder, stored_name)
            raise ServerException(f"Error while saving file: {e}") from e

    async def _process_and_save(self: Self, file: UploadFile, stored_name: str) -> int:
        return await self.file_repository.save_stream(
            self.sub_folder, stored_name, file.file
        )

    async def get_file_path(self: Self, user_id: uuid.UUID, file_id: uuid.UUID) -> str:
        """Получить публичный путь к файлу по id"""

        raw_metadata = await self.file_metadata_repository.get_or_none(file_id)
        if not raw_metadata:
            raise FileNotFoundException()

        metadata = file_schema.FileMetadata.model_validate(
            raw_metadata, from_attributes=True
        )

        if user_id != metadata.user_id:
            raise FileNotFoundException()

        file_path = self.file_repository.get_clear_path(
            self.sub_folder, metadata.stored_filename
        ).relative_to(self.file_repository._base_folder.absolute())

        return f"{self.public_url}/{file_path!s}"


class AvatarFileService(BaseFileService):
    async def validate_file(self, file: UploadFile) -> None:
        header = await file.read(2048)
        await file.seek(0)

        mime_type = magic.from_buffer(header, mime=True)
        if not mime_type.startswith("image/"):
            raise UnknownFileTypeException()

    async def _process_and_save(self, file: UploadFile, stored_name: str) -> int:
        """Перезаписываем этап сохранения файла, чтобы произвести ресайз"""
        content = await file.read()

        processed_content = await asyncio.to_thread(self._process_image, content)

        await self.file_repository.save(self.sub_folder, stored_name, processed_content)

        return len(processed_content)

    def _process_image(self, content: bytes) -> bytes:
        try:
            image = Image.open(io.BytesIO(content))

            result = ImageOps.fit(image, (200, 200), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            result.save(output, format="jpeg", quality=85)
            return output.getvalue()
        except UnidentifiedImageError:
            raise UnknownFileTypeException from UnidentifiedImageError
