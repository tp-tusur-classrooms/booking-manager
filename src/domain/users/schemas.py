from typing import Annotated, Self
import uuid

from pydantic import BaseModel, EmailStr, Field

from src.domain.base.joiner import WithSchema
from src.low.exceptions import (
    UserException,
)

_PASSWORD_PATTERN = r"^[A-Za-z0-9!#$%&*+\-.<=>?@^_]+$"
_NAME_PATTERN = r"^[A-Za-zА-ЯЁа-яё\- ]+$"

PasswordField = Annotated[
    str,
    Field(
        min_length=8, max_length=16, pattern=_PASSWORD_PATTERN, examples=["password"]
    ),
]
NameField = Annotated[str | None, Field(None, max_length=50, pattern=_NAME_PATTERN)]


# Repository
class CreateUser(BaseModel):
    email: str
    password: str
    name: str | None
    avatar_id: uuid.UUID | None


class UpdateUser(BaseModel):
    email: str | None = None
    password: str | None = None
    name: str | None = None
    avatar_id: uuid.UUID | None = None
    is_email_verified: bool | None = None


class FilterUser(BaseModel):
    id: list[uuid.UUID] | None = None
    email: str | None = None
    name: str | None = None


class UserWith(WithSchema):
    avatar: bool = False


# Base
class FullUser(BaseModel):
    id: uuid.UUID
    password: str
    email: EmailStr
    name: str | None
    avatar_url: str | None = None
    is_email_verified: bool = False


class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None
    avatar_url: str | None = None


class SignedUser(BaseModel):
    user: User
    token: str
    refresh_token: str


class PreviewUser(BaseModel):
    id: uuid.UUID
    name: str | None = None
    email: str


# API


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: PasswordField
    confirm_password: PasswordField
    accept_privacy: bool = False
    accept_terms: bool = False

    def passwords_match(self: Self) -> bool:
        return self.password == self.confirm_password

    def accepted_legal(self: Self) -> bool:
        return self.accept_privacy and self.accept_terms

    def validate_req(self: Self) -> None:
        if not self.accepted_legal():
            raise UserException("Нужно принять TOS и Политику конфиденциальности")

        if not self.passwords_match():
            raise UserException("Пароли должны совпадать")

    def to_create_user(self: Self) -> CreateUser:
        return CreateUser(
            email=self.email, password=self.password, name=None, avatar_id=None
        )


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: PasswordField


class SignedUserResponce(BaseModel):
    user: User
    token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshedTokenResponse(BaseModel):
    token: str


class UpdatePasswordRequest(BaseModel):
    old_password: PasswordField
    new_password: PasswordField
    confirm_password: PasswordField

    def passwords_match(self: Self) -> bool:
        return self.new_password == self.confirm_password


class UpdateUserRequest(BaseModel):
    name: NameField = None

    def to_update_user(self: Self, **extras: object) -> UpdateUser:
        data = self.model_dump(exclude_unset=True)
        data.update(extras)
        return UpdateUser.model_validate(data)
