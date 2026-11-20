import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from src.domain.common import models
from src.domain.file.repositories import FileRepository
from src.domain.rooms.photos import prepare_photo
from src.domain.rooms.repositories import RoomRepository
from src.domain.rooms.schemas import (
    Reference,
    ReferenceList,
    Room,
    RoomCreate,
    RoomList,
)
from src.low.database import UnitOfWork
from src.low.exceptions import FieldError, UserException

logger = logging.getLogger(__name__)


class RoomService:
    def __init__(
        self,
        uow: UnitOfWork,
        room_repository: RoomRepository,
        file_repository: FileRepository,
        public_url: str,
    ) -> None:
        self.uow = uow
        self.repository = room_repository
        self.files = file_repository
        self.public_url = public_url.rstrip("/")

    def _to_business(self, room: models.Room) -> Room:
        photo_url = None
        if room.photo:
            photo_url = "/".join(
                (self.public_url, room.photo.sub_folder, room.photo.stored_filename)
            )
        return Room(
            id=room.id,
            number=room.number,
            building=Reference.model_validate(room.building),
            floor=room.floor,
            capacity=room.capacity,
            equipment=[Reference.model_validate(item) for item in room.equipment],
            description=room.description,
            photo_url=photo_url,
        )

    async def buildings(self) -> ReferenceList:
        return ReferenceList(
            items=[
                Reference.model_validate(item)
                for item in await self.repository.buildings()
            ]
        )

    async def equipment(self) -> ReferenceList:
        return ReferenceList(
            items=[
                Reference.model_validate(item)
                for item in await self.repository.equipment()
            ]
        )

    async def list(self) -> RoomList:
        return RoomList(
            items=[self._to_business(room) for room in await self.repository.list()]
        )

    async def get(self, room_id: uuid.UUID) -> Room:
        return self._to_business(await self.repository.get(room_id))

    async def create(self, data: RoomCreate) -> Room:
        try:
            async with self.uow:
                return self._to_business(await self.repository.create(data))
        except IntegrityError as exc:
            # Проверка в БД также защищает от двух одновременных POST.
            constraint = getattr(exc.orig.__cause__, "constraint_name", None)
            if constraint != "uq_room_building_number":
                raise
            raise UserException(
                "Аудитория с таким номером уже есть в этом корпусе",
                status_code=409,
                code="room_number_taken",
                errors=[
                    FieldError(field="number", message="Номер уже занят в этом корпусе")
                ],
            ) from exc

    async def _remove_file(self, filename: str) -> None:
        try:
            await self.files.delete("rooms", filename)
        except OSError:
            logger.warning("Не удалось удалить фотографию %s", filename, exc_info=True)

    async def upload_photo(
        self, room_id: uuid.UUID, owner_id: uuid.UUID, file: UploadFile
    ) -> Room:
        stored_name = None
        previous = None
        try:
            async with self.uow:
                room = await self.repository.get(room_id, lock=True)
                content, extension = await prepare_photo(file)
                stored_name = f"{uuid.uuid4().hex}{extension}"
                await self.files.save("rooms", stored_name, content)
                previous = room.photo
                room.photo = models.File(
                    user_id=owner_id,
                    sub_folder="rooms",
                    original_filename=(file.filename or "photo")[:255],
                    stored_filename=stored_name,
                    size=len(content),
                )
                await self.repository.session.flush()
                if previous:
                    await self.repository.session.delete(previous)
                    await self.repository.session.flush()
                result = self._to_business(room)
        except BaseException:
            # Удаляем незакоммиченный файл также при отмене запроса.
            if stored_name:
                await self._remove_file(stored_name)
            raise
        if previous:
            await self._remove_file(previous.stored_filename)
        return result
