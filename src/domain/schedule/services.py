from collections import defaultdict
from datetime import date
import uuid

from sqlalchemy.exc import IntegrityError

from src.domain.common.models import ScheduledLesson
from src.domain.schedule.periods import UNIVERSITY_TIMEZONE, Period
from src.domain.schedule.repositories import ScheduleRepository
from src.domain.schedule.schemas import (
    ClassroomCalendar,
    DaySchedule,
    Lesson,
    LessonConflictError,
    LessonList,
    LessonWrite,
    RoomSummary,
    TeachingPeriod,
    TeachingPeriodList,
)
from src.low.database import UnitOfWork
from src.low.exceptions import FieldError, UserException


class LessonConflictException(UserException):
    def __init__(self, conflicts: list[Lesson]) -> None:
        super().__init__(
            "Аудитория уже занята в это время", status_code=409, code="lesson_conflict"
        )
        self.conflicts = conflicts

    def to_api(self) -> LessonConflictError:
        return LessonConflictError(
            message=self.public_message,
            status_code=self.status_code,
            code="lesson_conflict",
            conflicts=self.conflicts,
        )


class ScheduleService:
    def __init__(self, uow: UnitOfWork, repository: ScheduleRepository) -> None:
        self.uow = uow
        self.repository = repository

    @staticmethod
    def _to_business(lesson: ScheduledLesson) -> Lesson:
        return Lesson(
            id=lesson.id,
            room=RoomSummary.model_validate(lesson.room),
            period=TeachingPeriod.model_validate(lesson.period),
            date=lesson.date,
            starts_at=lesson.starts_at.astimezone(UNIVERSITY_TIMEZONE),
            ends_at=lesson.ends_at.astimezone(UNIVERSITY_TIMEZONE),
            subject=lesson.subject,
            group=lesson.group,
            teacher=lesson.teacher,
        )

    async def periods(self) -> TeachingPeriodList:
        return TeachingPeriodList(
            items=[
                TeachingPeriod.model_validate(period)
                for period in await self.repository.periods()
            ]
        )

    async def lessons(self, day: date | None = None) -> LessonList:
        return LessonList(
            items=[
                self._to_business(lesson)
                for lesson in await self.repository.lessons(day)
            ]
        )

    async def get(self, lesson_id: uuid.UUID) -> Lesson:
        return self._to_business(await self.repository.get(lesson_id))

    async def schedule(self, day: date) -> DaySchedule:
        periods = await self.periods()
        rooms = await self.repository.rooms()
        lessons = await self.lessons(day)
        by_room: dict[uuid.UUID, list[Lesson]] = defaultdict(list)
        for lesson in lessons.items:
            by_room[lesson.room.id].append(lesson)
        bounds = Period.day(day)
        return DaySchedule(
            date=day,
            timezone=UNIVERSITY_TIMEZONE.key,
            starts_at=bounds.starts_at,
            ends_at=bounds.ends_at,
            periods=periods.items,
            items=[
                ClassroomCalendar(
                    room=RoomSummary.model_validate(room), lessons=by_room[room.id]
                )
                for room in rooms
            ],
        )

    async def save(
        self, data: LessonWrite, lesson_id: uuid.UUID | None = None
    ) -> Lesson:
        interval = None
        try:
            async with self.uow:
                lesson = (
                    await self.repository.get(lesson_id, lock=True)
                    if lesson_id
                    else None
                )
                room, period = await self.repository.references(data)
                interval = Period.on_date(data.date, period.start_time, period.end_time)
                saved = await self.repository.save(data, room, period, interval, lesson)
                return self._to_business(saved)
        except IntegrityError as exc:
            constraint = getattr(exc.orig.__cause__, "constraint_name", None)
            if constraint == "ex_scheduled_lesson_overlap" and interval is not None:
                conflicts = await self.repository.conflicts(
                    data.room_id, interval, lesson_id
                )
                raise LessonConflictException(
                    [self._to_business(item) for item in conflicts]
                ) from exc
            field = {
                "fk_scheduled_lesson_room": "room_id",
                "fk_scheduled_lesson_period": "period_id",
            }.get(constraint)
            if field:
                raise UserException(
                    "Проверьте заполнение полей",
                    errors=[
                        FieldError(field=field, message="Запись справочника не найдена")
                    ],
                ) from exc
            raise

    async def delete(self, lesson_id: uuid.UUID) -> None:
        async with self.uow:
            await self.repository.delete(
                await self.repository.get(lesson_id, lock=True)
            )
