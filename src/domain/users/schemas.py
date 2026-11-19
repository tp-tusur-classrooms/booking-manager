from typing import Annotated, Literal, Self
import uuid

from pydantic import AfterValidator, BaseModel, EmailStr, Field, field_validator

from src.domain.base.joiner import WithSchema
from src.low.exceptions import (
    FieldError,
    UserException,
)

_PASSWORD_PATTERN = r"^[A-Za-z0-9!#$%&*+\-.<=>?@^_]+$"
_NAME_PATTERN = r"^[A-Za-zА-ЯЁа-яё\- ]+$"
Role = Literal["user", "admin"]

PasswordField = Annotated[
    str,
    Field(
        min_length=8, max_length=16, pattern=_PASSWORD_PATTERN, examples=["password"]
    ),
]
NameField = Annotated[str, Field(min_length=1, max_length=50, pattern=_NAME_PATTERN)]
LoginField = Annotated[
    str,
    Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"),
    AfterValidator(str.lower),
]


# Схемы репозитория
class CreateUser(BaseModel):
    login: LoginField
    role: Role = "user"
    email: str | None = None
    password: str
    name: str
    avatar_id: uuid.UUID | None = None


class UpdateUser(BaseModel):
    email: str | None = None
    password: str | None = None
    name: str | None = None
    avatar_id: uuid.UUID | None = None
    is_email_verified: bool | None = None


class FilterUser(BaseModel):
    id: list[uuid.UUID] | None = None
    email: str | None = None
    login: str | None = None
    name: str | None = None


class UserWith(WithSchema):
    avatar: bool = False


# Основные схемы
class FullUser(BaseModel):
    id: uuid.UUID
    password: str
    email: EmailStr | None = None
    login: str
    role: Role
    name: str
    avatar_url: str | None = None
    is_email_verified: bool = False


class User(BaseModel):
    id: uuid.UUID
    login: str
    role: Role
    name: str
    email: EmailStr | None = None
    avatar_url: str | None = None


class SignedUser(BaseModel):
    user: User
    token: str
    refresh_token: str


class PreviewUser(BaseModel):
    id: uuid.UUID
    name: str | None = None
    email: str


# Запросы и ответы API


class RegisterUserRequest(BaseModel):
    name: NameField
    login: LoginField
    password: PasswordField
    confirm_password: str

    def passwords_match(self: Self) -> bool:
        return self.password == self.confirm_password

    def validate_req(self: Self) -> None:
        if not self.passwords_match():
            raise UserException(
                "Проверьте заполнение полей",
                code="validation_error",
                errors=[
                    FieldError(
                        field="confirm_password", message="Пароли должны совпадать"
                    )
                ],
            )

    def to_create_user(self: Self) -> CreateUser:
        return CreateUser(
            login=self.login, password=self.password, name=self.name, role="user"
        )


class LoginUserRequest(BaseModel):
    login: Annotated[str, Field(min_length=1), AfterValidator(str.lower)]
    password: str = Field(min_length=1)


class SignedUserResponce(BaseModel):
    user: User
    token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class RefreshedTokenResponse(BaseModel):
    token: str


class UpdatePasswordRequest(BaseModel):
    old_password: PasswordField
    new_password: PasswordField
    confirm_password: PasswordField

    def passwords_match(self: Self) -> bool:
        return self.new_password == self.confirm_password


class UpdateUserRequest(BaseModel):
    name: NameField | None = None

    @field_validator("name")
    @classmethod
    def name_cannot_be_cleared(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Имя не может быть пустым")
        return value

    def to_update_user(self: Self, **extras: object) -> UpdateUser:
        data = self.model_dump(exclude_unset=True)
        data.update(extras)
        return UpdateUser.model_validate(data)
