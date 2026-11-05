from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict


class TokenType(StrEnum):
    PASSWORD_RESET = "PASSWORD_RESET"
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    EMAIL_CHANGE = "EMAIL_CHANGE"


# Repo
class CreateToken(BaseModel):
    user_id: uuid.UUID
    code: str
    type: TokenType
    expires_at: datetime
    payload: dict[str, Any] | None = None


class UpdateToken(BaseModel):
    used: bool


class FilterToken(BaseModel):
    user_id: uuid.UUID
    code: str
    type: TokenType
    used: bool


# Base
class TokenBase(BaseModel):
    user_id: uuid.UUID
    code: str
    type: TokenType
    expires_at: datetime
    used: bool = False
    payload: dict[str, Any] | None = None

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at


class Token(TokenBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
