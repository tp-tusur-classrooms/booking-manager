import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Security

from src.api.v1.common import get_current_user, require_admin
from src.domain.schedule.schemas import (
    CalendarDate,
    DaySchedule,
    Lesson,
    LessonConflictError,
    LessonList,
    LessonWrite,
    TeachingPeriodList,
)
from src.domain.schedule.services import ScheduleService
from src.low.container import Container
from src.low.exceptions import APIException

router = APIRouter(
    tags=["Schedule"],
    dependencies=[Security(get_current_user)],
    responses={401: {"model": APIException}},
)


@router.get("/periods", operation_id="listPeriods")
@inject
async def list_periods(
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> TeachingPeriodList:
    """Общий справочник; количество периодов не фиксировано макетом."""
    return await service.periods()


@router.get(
    "/schedule", operation_id="getDaySchedule", responses={400: {"model": APIException}}
)
@inject
async def get_schedule(
    date: CalendarDate,
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> DaySchedule:
    """Все опубликованные аудитории, в том числе без занятий, за сутки Asia/Tomsk."""
    return await service.schedule(date)


@router.get(
    "/lessons", operation_id="listLessons", responses={400: {"model": APIException}}
)
@inject
async def list_lessons(
    date: CalendarDate | None = None,
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> LessonList:
    return await service.lessons(date)


@router.get(
    "/lessons/{lesson_id}",
    operation_id="getLesson",
    responses={status: {"model": APIException} for status in (400, 404)},
)
@inject
async def get_lesson(
    lesson_id: uuid.UUID,
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> Lesson:
    return await service.get(lesson_id)


@router.post(
    "/lessons",
    operation_id="createLesson",
    status_code=201,
    dependencies=[Security(require_admin)],
    responses={
        400: {"model": APIException},
        403: {"model": APIException},
        409: {"model": LessonConflictError},
    },
)
@inject
async def create_lesson(
    data: LessonWrite,
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> Lesson:
    return await service.save(data)


@router.put(
    "/lessons/{lesson_id}",
    operation_id="updateLesson",
    dependencies=[Security(require_admin)],
    responses={
        **{status: {"model": APIException} for status in (400, 403, 404)},
        409: {"model": LessonConflictError},
    },
)
@inject
async def update_lesson(
    lesson_id: uuid.UUID,
    data: LessonWrite,
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> Lesson:
    """Заменяет одно конкретное занятие; запись не конфликтует сама с собой."""
    return await service.save(data, lesson_id)


@router.delete(
    "/lessons/{lesson_id}",
    operation_id="deleteLesson",
    status_code=204,
    dependencies=[Security(require_admin)],
    responses={status: {"model": APIException} for status in (400, 403, 404)},
)
@inject
async def delete_lesson(
    lesson_id: uuid.UUID,
    service: ScheduleService = Depends(Provide[Container.schedule_service]),
) -> None:
    await service.delete(lesson_id)
