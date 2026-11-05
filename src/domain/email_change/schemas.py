from datetime import UTC, datetime
from typing import Self
import uuid

from pydantic import BaseModel, EmailStr


class EmailChangeRequest(BaseModel):
    new_email: EmailStr


class EmailChangeConfirm(BaseModel):
    code: str


class CreateEmailChange(BaseModel):
    user_id: uuid.UUID
    new_email: str
    code: str
    expires_at: datetime


class UpdateEmailChange(BaseModel):
    used: bool | None = None


class FilterEmailChange(BaseModel):
    id: list[uuid.UUID] | None = None
    user_id: uuid.UUID | None = None
    code: str | None = None
    used: bool | None = None


class EmailChange(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    new_email: str
    code: str
    expires_at: datetime
    used: bool

    def is_expired(self: Self) -> bool:
        now = datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at < now
