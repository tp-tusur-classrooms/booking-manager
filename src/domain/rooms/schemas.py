from typing import Annotated, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

RoomNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)
]


class Reference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ReferenceList(BaseModel):
    items: list[Reference]


class RoomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: RoomNumber
    building_id: uuid.UUID
    floor: int = Field(strict=True, ge=-5, le=50)
    capacity: int = Field(strict=True, ge=1, le=1000)
    equipment_ids: list[uuid.UUID] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("equipment_ids")
    @classmethod
    def unique_equipment(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Оборудование не должно повторяться")
        return value


class Room(BaseModel):
    id: uuid.UUID
    number: str
    building: Reference
    floor: int
    capacity: int
    equipment: list[Reference]
    description: str | None
    photo_url: str | None
    status: Literal["published"]


class RoomList(BaseModel):
    items: list[Room]
