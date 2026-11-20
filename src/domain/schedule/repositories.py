from datetime import date
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.common.models import (
    Building,
    Room,
    ScheduledLesson,
    TeachingPeriodTemplate,
)
from src.domain.schedule.periods import Period
from src.domain.schedule.schemas import LessonWrite
from src.low.exceptions import FieldError, NotFoundException, UserException


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def periods(self) -> list[TeachingPeriodTemplate]:
        return list(
            await self.session.scalars(
                select(TeachingPeriodTemplate).order_by(TeachingPeriodTemplate.order)
            )
        )

    async def rooms(self) -> list[Room]:
        # Все аудитории BE-02 публикуются сразу; пустые строки тоже нужны календарю.
        return list(
            await self.session.scalars(
                select(Room)
                .join(Room.building)
                .options(selectinload(Room.building))
                .order_by(Building.name, Room.number, Room.id)
            )
        )

    @staticmethod
    def _loaded() -> tuple:
        return (
            selectinload(ScheduledLesson.room).selectinload(Room.building),
            selectinload(ScheduledLesson.period),
        )

    async def lessons(self, day: date | None = None) -> list[ScheduledLesson]:
        query = (
            select(ScheduledLesson)
            .join(ScheduledLesson.room)
            .join(Room.building)
            .options(*self._loaded())
            .order_by(
                ScheduledLesson.date,
                ScheduledLesson.starts_at,
                Building.name,
                Room.number,
                ScheduledLesson.id,
            )
        )
        if day is not None:
            bounds = Period.day(day)
            query = query.where(
                ScheduledLesson.starts_at >= bounds.starts_at,
                ScheduledLesson.starts_at < bounds.ends_at,
            )
        return list(await self.session.scalars(query))

    async def get(self, lesson_id: uuid.UUID, *, lock: bool = False) -> ScheduledLesson:
        query = (
            select(ScheduledLesson)
            .where(ScheduledLesson.id == lesson_id)
            .options(*self._loaded())
        )
        if lock:
            query = query.with_for_update()
        lesson = await self.session.scalar(query)
        if lesson is None:
            raise NotFoundException("Занятие не найдено")
        return lesson

    async def references(
        self, data: LessonWrite
    ) -> tuple[Room, TeachingPeriodTemplate]:
        room = await self.session.scalar(
            select(Room)
            .where(Room.id == data.room_id)
            .options(selectinload(Room.building))
        )
        period = await self.session.scalar(
            select(TeachingPeriodTemplate)
            .where(TeachingPeriodTemplate.id == data.period_id)
            .with_for_update(read=True)
        )
        errors = []
        if room is None:
            errors.append(
                FieldError(field="room_id", message="Выберите существующую аудиторию")
            )
        if period is None:
            errors.append(
                FieldError(field="period_id", message="Выберите период из справочника")
            )
        if errors:
            raise UserException("Проверьте заполнение полей", errors=errors)
        assert room is not None and period is not None
        return room, period

    async def save(
        self,
        data: LessonWrite,
        room: Room,
        period: TeachingPeriodTemplate,
        interval: Period,
        lesson: ScheduledLesson | None,
    ) -> ScheduledLesson:
        if lesson is None:
            lesson = ScheduledLesson()
        lesson.room = room
        lesson.period = period
        lesson.date = data.date
        lesson.starts_at, lesson.ends_at = interval.starts_at, interval.ends_at
        lesson.subject, lesson.group, lesson.teacher = (
            data.subject,
            data.group,
            data.teacher,
        )
        self.session.add(lesson)
        await self.session.flush()
        await self.session.refresh(lesson, attribute_names=["starts_at", "ends_at"])
        return lesson

    async def conflicts(
        self,
        room_id: uuid.UUID,
        interval: Period,
        exclude_id: uuid.UUID | None,
    ) -> list[ScheduledLesson]:
        query = (
            select(ScheduledLesson)
            .where(
                ScheduledLesson.room_id == room_id,
                ScheduledLesson.starts_at < interval.ends_at,
                ScheduledLesson.ends_at > interval.starts_at,
            )
            .options(*self._loaded())
            .order_by(ScheduledLesson.starts_at, ScheduledLesson.id)
        )
        if exclude_id is not None:
            query = query.where(ScheduledLesson.id != exclude_id)
        return list(await self.session.scalars(query))

    async def delete(self, lesson: ScheduledLesson) -> None:
        await self.session.delete(lesson)
        await self.session.flush()
