from typing import Self
import uuid

from fastapi import UploadFile

from src.domain.base.base_service import BaseService
from src.domain.common import models
from src.domain.email_verification.services import EmailVerificationService
import src.domain.file.schemas as file_schemas
from src.domain.file.services import AvatarFileService
from src.domain.security.services import HasherService, TokenService
from src.domain.users.repositories import UserRepository
import src.domain.users.schemas as user_schemas
from src.low.database import UnitOfWork
from src.low.exceptions import (
    DublicateException,
    NotFoundException,
    UnauthorizatedException,
    UserException,
)


class UserService(BaseService):
    """
    Сервис управления пользователями.

    Отвечает за регистрацию, вход и управление профилем пользователя.
    """

    def __init__(
        self: Self,
        uow: UnitOfWork,
        user_repository: UserRepository,
        hasher_service: HasherService,
        token_service: TokenService,
        avatar_file_service: AvatarFileService,
        email_verification_service: EmailVerificationService,
    ) -> None:
        self.uow = uow
        self.user_repository: UserRepository = user_repository
        self.hasher_service = hasher_service
        self.token_service = token_service
        self.avatar_file_service = avatar_file_service
        self.email_verification_service: EmailVerificationService = (
            email_verification_service
        )

    # Helpers & converters
    def _with(self: Self) -> user_schemas.UserWith:
        return user_schemas.UserWith(avatar=True)

    async def _to_business(self: Self, model: models.User) -> user_schemas.User:
        public_user = user_schemas.User.model_validate(model, from_attributes=True)

        if model.avatar_id:
            avatar = file_schemas.FileMetadata.model_validate(
                model.avatar, from_attributes=True
            )
            public_user.avatar_url = await self.avatar_file_service.get_file_path(
                model.id, avatar.id
            )

        return public_user

    async def _to_business_full(
        self: Self, model: models.User
    ) -> user_schemas.FullUser:
        public_user = user_schemas.FullUser.model_validate(model, from_attributes=True)

        if model.avatar_id:
            avatar = file_schemas.FileMetadata.model_validate(
                model.avatar, from_attributes=True
            )
            public_user.avatar_url = await self.avatar_file_service.get_file_path(
                model.id, avatar.id
            )

        return public_user

    def _to_signed_user_responce(
        self: Self, user: user_schemas.User
    ) -> user_schemas.SignedUserResponce:
        token_data = {"sub": str(user.id)}
        return user_schemas.SignedUserResponce(
            user=user,
            token=self.token_service.create_access_token(token_data),
            refresh_token=self.token_service.create_refresh_token(token_data),
        )

    # Domain operations
    # Get
    async def get_by_id(self: Self, user_id: uuid.UUID) -> user_schemas.User:
        user = await self.user_repository.get(id=user_id, with_schema=self._with())

        return await self._to_business(user)

    async def get_by_email(self: Self, email: str) -> user_schemas.User:
        filters = user_schemas.FilterUser(email=email)
        first = await self.user_repository.get_first(filters, with_schema=self._with())

        return await self._to_business(first)

    async def get_by_email_or_none(self: Self, email: str) -> user_schemas.User | None:
        try:
            return await self.get_by_email(email)
        except NotFoundException:
            return None

    async def get_by_token(self: Self, token: str) -> user_schemas.User:
        try:
            user_id = self.token_service.get_user_id_from_token(token)
            return await self.get_by_id(user_id)
        except (NotFoundException, UnauthorizatedException) as e:
            raise UnauthorizatedException from e

    # Get full
    async def get_full_by_id(self: Self, id: uuid.UUID) -> user_schemas.FullUser:
        try:
            first = await self.user_repository.get(id, with_schema=self._with())
        except NotFoundException as e:
            raise UserException("Пользователя не существует") from e

        return await self._to_business_full(first)

    async def get_full_by_email(self: Self, email: str) -> user_schemas.FullUser:
        filters = user_schemas.FilterUser(email=email)
        try:
            first = await self.user_repository.get_first(
                filters, with_schema=self._with()
            )
        except NotFoundException as e:
            raise UserException("Пользователя не существует") from e

        return await self._to_business_full(first)

    # Create
    async def create(
        self: Self, create_user: user_schemas.CreateUser
    ) -> user_schemas.User:
        try:
            new_raw_user = await self.user_repository.create(create_user)
        except DublicateException as e:
            raise DublicateException("Email уже занят") from e

        return await self._to_business(new_raw_user)

    async def update(
        self: Self, user_id: uuid.UUID, update_data: user_schemas.UpdateUser
    ) -> None:
        await self.user_repository.update(user_id, update_data)

    async def exists(self: Self, user_id: uuid.UUID) -> bool:
        return await self.user_repository.exists(user_id)

    async def set_password(self: Self, user_id: uuid.UUID, new_password: str) -> None:
        hashed_password = self.hasher_service.get_password_hash(new_password)

        user_update = user_schemas.UpdateUser(password=hashed_password)
        await self.update(user_id, user_update)

    # Use cases
    async def register(
        self: Self, create_user: user_schemas.RegisterUserRequest
    ) -> user_schemas.SignedUserResponce:
        async with self.uow:
            create_data = create_user.to_create_user()
            create_data.password = self.hasher_service.get_password_hash(
                create_data.password
            )
            new_user = await self.create(create_data)

            await self.email_verification_service.create_challenge(
                new_user.id, new_user.email
            )

            return self._to_signed_user_responce(new_user)

    async def login(
        self: Self, data: user_schemas.LoginUserRequest
    ) -> user_schemas.SignedUserResponce:
        full_user = await self.get_full_by_email(data.email)

        if not self.hasher_service.validate_password(data.password, full_user.password):
            raise UnauthorizatedException()

        user = await self.get_by_email(data.email)

        return self._to_signed_user_responce(user)

    async def patch_profile(
        self: Self,
        user_id: uuid.UUID,
        update_data: user_schemas.UpdateUserRequest,
        avatar: UploadFile | None,
        clear_avatar: bool,
    ) -> None:
        async with self.uow:
            extras: dict[str, object] = {}
            if clear_avatar:
                extras["avatar_id"] = None
            elif avatar is not None and avatar.filename:
                saved = await self.avatar_file_service.save(user_id, avatar)
                extras["avatar_id"] = saved.id

            if not extras and not update_data.model_fields_set:
                return

            await self.update(user_id, update_data.to_update_user(**extras))

    async def update_password(
        self: Self, user_id: uuid.UUID, update_data: user_schemas.UpdatePasswordRequest
    ) -> None:
        user = await self.get_full_by_id(user_id)

        if not self.hasher_service.validate_password(
            update_data.old_password, user.password
        ):
            raise UserException("Неверный текущий пароль")

        if not update_data.passwords_match():
            raise UserException("Пароли должны совпадать")
        async with self.uow:
            await self.set_password(user.id, update_data.new_password)

    async def verify_email(self: Self, user_id: uuid.UUID, code: str) -> None:
        async with self.uow:
            await self.email_verification_service.verify_email(user_id, code)

            await self.update(user_id, user_schemas.UpdateUser(is_email_verified=True))
