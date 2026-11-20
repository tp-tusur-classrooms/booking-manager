from datetime import date, datetime, time, timedelta
import re
from typing import Annotated, Literal
import uuid

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
)

from src.domain.rooms.schemas import Reference
from src.low.exceptions import APIException


def calendar_date(value: object) -> object:
    if isinstance(value, str):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
    elif isinstance(value, date) and not isinstance(value, datetime):
        return value
    raise ValueError("Укажите дату в формате ГГГГ-ММ-ДД")


CalendarDate = Annotated[
    date, BeforeValidator(calendar_date), Field(le=date.max - timedelta(days=1))
]
LessonName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class TeachingPeriod(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order: int
    start_time: time
    end_time: time

    @field_serializer("start_time", "end_time")
    def format_time(self, value: time) -> str:
        return value.strftime("%H:%M")


class TeachingPeriodList(BaseModel):
    items: list[TeachingPeriod]


class RoomSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: str
    building: Reference


class LessonWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: uuid.UUID
    period_id: uuid.UUID
    date: CalendarDate
    subject: LessonName
    group: LessonName | None = None
    teacher: LessonName | None = None


class Lesson(BaseModel):
    id: uuid.UUID
    room: RoomSummary
    period: TeachingPeriod
    date: date
    starts_at: datetime
    ends_at: datetime
    subject: str
    group: str | None
    teacher: str | None


class LessonList(BaseModel):
    items: list[Lesson]


class ClassroomCalendar(BaseModel):
    """Строка календаря; новые виды занятости можно добавить отдельными полями."""

    room: RoomSummary
    lessons: list[Lesson]


class DaySchedule(BaseModel):
    date: date
    timezone: Literal["Asia/Tomsk"]
    starts_at: datetime
    ends_at: datetime
    periods: list[TeachingPeriod]
    items: list[ClassroomCalendar]


class LessonConflictError(APIException):
    conflicts: list[Lesson] = Field(default_factory=list)
