from datetime import UTC, datetime
from typing import Self
import uuid

from pydantic import BaseModel, EmailStr

from src.domain.users.schemas import PasswordField


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: PasswordField
    confirm_password: str

    def passwords_match(self: Self) -> bool:
        return self.new_password == self.confirm_password


class ChangePasswordRequest(BaseModel):
    old_password: PasswordField
    new_password: PasswordField
    confirm_password: PasswordField

    def passwords_match(self: Self) -> bool:
        return self.new_password == self.confirm_password


class CreatePasswordReset(BaseModel):
    user_id: uuid.UUID
    code: str
    expires_at: datetime


class UpdatePasswordReset(BaseModel):
    used: bool | None = None
    attempts: int | None = None


class FilterPasswordReset(BaseModel):
    id: list[uuid.UUID] | None = None
    user_id: uuid.UUID | None = None
    code: str | None = None
    used: bool | None = None


class PasswordReset(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    code: str
    expires_at: datetime
    used: bool

    def is_expired(self: Self) -> bool:
        """
        Проверяем, не истек ли код
        """

        now = datetime.now(UTC)
        expires_at = self.expires_at

        return expires_at < now
