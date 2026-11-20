import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.common.models import Building, Equipment, Room
from src.domain.rooms.schemas import RoomCreate
from src.low.exceptions import FieldError, NotFoundException, UserException


class RoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def buildings(self) -> list[Building]:
        return list(
            await self.session.scalars(select(Building).order_by(Building.name))
        )

    async def equipment(self) -> list[Equipment]:
        return list(
            await self.session.scalars(select(Equipment).order_by(Equipment.name))
        )

    @staticmethod
    def _loaded() -> tuple:
        return (
            selectinload(Room.building),
            selectinload(Room.equipment),
            selectinload(Room.photo),
        )

    async def list(self) -> list[Room]:
        query = (
            select(Room)
            .join(Room.building)
            .options(*self._loaded())
            .order_by(Building.name, Room.number, Room.id)
        )
        return list(await self.session.scalars(query))

    async def get(self, room_id: uuid.UUID, *, lock: bool = False) -> Room:
        query = select(Room).where(Room.id == room_id).options(*self._loaded())
        if lock:
            query = query.with_for_update()
        room = await self.session.scalar(query)
        if room is None:
            raise NotFoundException("Аудитория не найдена")
        return room

    async def create(self, data: RoomCreate) -> Room:
        building = await self.session.get(Building, data.building_id)
        equipment = list(
            await self.session.scalars(
                select(Equipment)
                .where(Equipment.id.in_(data.equipment_ids))
                .order_by(Equipment.name)
            )
        )
        errors = []
        if building is None:
            errors.append(
                FieldError(field="building_id", message="Выберите корпус из списка")
            )
        if len(equipment) != len(data.equipment_ids):
            errors.append(
                FieldError(
                    field="equipment_ids", message="Выберите оборудование из списка"
                )
            )
        if errors:
            raise UserException("Проверьте заполнение полей", errors=errors)
        room = Room(
            number=data.number,
            building=building,
            floor=data.floor,
            capacity=data.capacity,
            description=data.description,
            equipment=equipment,
            photo=None,
        )
        self.session.add(room)
        await self.session.flush()
        return room
