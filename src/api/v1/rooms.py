import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Security, UploadFile

from src.api.v1.common import get_current_user, require_admin
from src.domain.rooms.schemas import ReferenceList, Room, RoomCreate, RoomList
from src.domain.rooms.services import RoomService
from src.domain.users.schemas import User
from src.low.container import Container
from src.low.exceptions import APIException

router = APIRouter(
    dependencies=[Security(get_current_user)], responses={401: {"model": APIException}}
)


@router.get("/buildings", tags=["References"], operation_id="listBuildings")
@inject
async def list_buildings(
    service: RoomService = Depends(Provide[Container.room_service]),
) -> ReferenceList:
    return await service.buildings()


@router.get("/equipment", tags=["References"], operation_id="listEquipment")
@inject
async def list_equipment(
    service: RoomService = Depends(Provide[Container.room_service]),
) -> ReferenceList:
    return await service.equipment()


@router.get("/rooms", tags=["Rooms"], operation_id="listRooms")
@inject
async def list_rooms(
    service: RoomService = Depends(Provide[Container.room_service]),
) -> RoomList:
    """Каталог для пользователя и список управления для администратора."""
    return await service.list()


@router.post(
    "/rooms",
    tags=["Rooms"],
    operation_id="createRoom",
    status_code=201,
    dependencies=[Security(require_admin)],
    responses={status: {"model": APIException} for status in (400, 403, 409)},
)
@inject
async def create_room(
    data: RoomCreate,
    service: RoomService = Depends(Provide[Container.room_service]),
) -> Room:
    """Создаёт аудиторию, сразу видимую в пользовательском каталоге."""
    return await service.create(data)


@router.get(
    "/rooms/{room_id}",
    tags=["Rooms"],
    operation_id="getRoom",
    responses={status: {"model": APIException} for status in (400, 404)},
)
@inject
async def get_room(
    room_id: uuid.UUID,
    service: RoomService = Depends(Provide[Container.room_service]),
) -> Room:
    return await service.get(room_id)


@router.post(
    "/rooms/{room_id}/publish",
    tags=["Rooms"],
    operation_id="publishRoom",
    deprecated=True,
    dependencies=[Security(require_admin)],
    responses={status: {"model": APIException} for status in (400, 403, 404)},
)
@inject
async def publish_room(
    room_id: uuid.UUID,
    service: RoomService = Depends(Provide[Container.room_service]),
) -> Room:
    """Совместимость со старым клиентом: аудитория уже опубликована при создании."""
    return await service.get(room_id)


@router.put(
    "/rooms/{room_id}/photo",
    tags=["Rooms"],
    operation_id="uploadRoomPhoto",
    responses={status: {"model": APIException} for status in (400, 403, 404, 413, 415)},
)
@inject
async def upload_room_photo(
    room_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Security(require_admin),
    service: RoomService = Depends(Provide[Container.room_service]),
) -> Room:
    """Заменить фото: JPG/PNG по содержимому, не больше 10 МБ."""
    return await service.upload_photo(room_id, current_user.id, file)
