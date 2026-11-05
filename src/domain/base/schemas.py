from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any, Self

from fastapi_pagination.cursor import CursorPage
from pydantic import BaseModel
from sqlalchemy import asc, desc

from src.domain.common import models


class Success(BaseModel):
    message: str = "Success"
    status_code: int = 200


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"

    def _sort_function(self: Self) -> Any:
        if self == OrderDirection.ASC:
            return asc
        return desc


class SortClause(BaseModel):
    field: str
    direction: OrderDirection


class OrderBy:
    def __init__(self: Self, **kwargs: OrderDirection) -> None:
        self.clauses: list[SortClause] = []

        for field, direction in kwargs.items():
            self.clauses.append(SortClause(field=field, direction=direction))


class CursorPageResponce[T: BaseModel](BaseModel):
    items: Sequence[T]
    next_page: str | None
    previous_page: str | None

    @classmethod
    def create_empty[N: BaseModel](cls) -> "CursorPageResponce[N]":
        return CursorPageResponce[N](items=[], next_page=None, previous_page=None)


def cursor_converter[In: models.Base, Out: BaseModel](
    raw_cursor: CursorPage[In],
    target: type[Out],
    converter: Callable[[In], Out] | None = None,
) -> CursorPageResponce[Out]:
    if converter is None:
        converter = lambda el: target.model_validate(el, from_attributes=True)  # noqa: E731

    items = [converter(item) for item in raw_cursor.items]

    return CursorPageResponce[Out](
        items=items,
        next_page=raw_cursor.next_page,
        previous_page=raw_cursor.previous_page,
    )
