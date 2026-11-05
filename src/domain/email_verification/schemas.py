from datetime import UTC, datetime
from typing import Self
import uuid

from pydantic import BaseModel


class ConfirmEmailVerification(BaseModel):
    code: str


class CreateEmailVerification(BaseModel):
    user_id: uuid.UUID
    code: str
    expires_at: datetime


class UpdateEmailVerification(BaseModel):
    used: bool | None = None


class FilterEmailVerification(BaseModel):
    id: list[uuid.UUID] | None = None
    user_id: uuid.UUID | None = None
    code: str | None = None
    used: bool | None = None


class EmailVerification(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    code: str
    expires_at: datetime
    used: bool

    def is_expired(self: Self) -> bool:
        now = datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at < now
