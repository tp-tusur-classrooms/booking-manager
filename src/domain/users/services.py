from datetime import UTC, datetime
from typing import Self
import uuid

from src.domain.base.base_service import BaseService
from src.domain.common import models
from src.domain.security.services import HasherService, TokenService
from src.domain.token.repositories import TokenRepository
from src.domain.users.repositories import UserRepository
import src.domain.users.schemas as user_schemas
from src.low.database import UnitOfWork
from src.low.exceptions import (
    DublicateException,
    FieldError,
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
        token_repository: TokenRepository,
    ) -> None:
        self.uow = uow
        self.user_repository: UserRepository = user_repository
        self.hasher_service = hasher_service
        self.token_service = token_service
        self.token_repository = token_repository

    # Вспомогательные методы и преобразования
    def _to_business(self: Self, model: models.User) -> user_schemas.User:
        return user_schemas.User.model_validate(model, from_attributes=True)

    def _to_business_full(self: Self, model: models.User) -> user_schemas.FullUser:
        return user_schemas.FullUser.model_validate(model, from_attributes=True)

    def _to_signed_user_responce(
        self: Self, user: user_schemas.User
    ) -> user_schemas.SignedUserResponce:
        token_data = {"sub": str(user.id)}
        return user_schemas.SignedUserResponce(
            user=user,
            token=self.token_service.create_access_token(token_data),
            refresh_token=self.token_service.create_refresh_token(token_data),
        )

    # Операции с пользователями
    # Получение пользователя
    async def get_by_id(self: Self, user_id: uuid.UUID) -> user_schemas.User:
        user = await self.user_repository.get(id=user_id)
        return self._to_business(user)

    async def get_by_token(self: Self, token: str) -> user_schemas.User:
        try:
            user_id = self.token_service.get_user_id_from_token(token)
            return await self.get_by_id(user_id)
        except NotFoundException as e:
            raise UnauthorizatedException from e

    # Получение полных данных пользователя
    async def get_full_by_id(self: Self, id: uuid.UUID) -> user_schemas.FullUser:
        try:
            first = await self.user_repository.get(id)
        except NotFoundException as e:
            raise UserException("Пользователя не существует") from e

        return self._to_business_full(first)

    # Создание пользователя
    async def create(
        self: Self, create_user: user_schemas.CreateUser
    ) -> user_schemas.User:
        try:
            new_raw_user = await self.user_repository.create(create_user)
        except DublicateException as e:
            raise UserException(
                "Такой логин уже занят",
                status_code=409,
                code="login_taken",
                errors=[FieldError(field="login", message="Такой логин уже занят")],
            ) from e

        return self._to_business(new_raw_user)

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

    # Пользовательские сценарии
    async def register(
        self: Self, create_user: user_schemas.RegisterUserRequest
    ) -> user_schemas.User:
        create_user.validate_req()
        async with self.uow:
            create_data = create_user.to_create_user()
            create_data.password = self.hasher_service.get_password_hash(
                create_data.password
            )
            return await self.create(create_data)

    async def login(
        self: Self, data: user_schemas.LoginUserRequest
    ) -> user_schemas.SignedUserResponce:
        try:
            model = await self.user_repository.get_first(
                user_schemas.FilterUser(login=data.login)
            )
        except NotFoundException:
            model = None

        if model is None or not self.hasher_service.validate_password(
            data.password, model.password
        ):
            raise UnauthorizatedException(
                "Не удалось войти. Проверьте логин и пароль.", "invalid_credentials"
            )

        user = self._to_business(model)

        return self._to_signed_user_responce(user)

    async def refresh(self: Self, token: str) -> user_schemas.RefreshedTokenResponse:
        try:
            user_id = self.token_service.get_user_id_from_refresh_token(token)
            token_id = uuid.UUID(str(self.token_service.decode_token(token)["jti"]))
            await self.user_repository.get(user_id)
        except (UnauthorizatedException, NotFoundException, ValueError) as exc:
            raise UnauthorizatedException(
                "Сессия истекла. Войдите снова.", "invalid_refresh_token"
            ) from exc
        if await self.token_repository.is_refresh_revoked(token_id):
            raise UnauthorizatedException(
                "Сессия истекла. Войдите снова.", "invalid_refresh_token"
            )
        return user_schemas.RefreshedTokenResponse(
            token=self.token_service.create_access_token({"sub": str(user_id)})
        )

    async def logout(self: Self, token: str) -> None:
        try:
            self.token_service.get_user_id_from_refresh_token(token)
            payload = self.token_service.decode_token(token)
            token_id = uuid.UUID(str(payload["jti"]))
            expires_at = datetime.fromtimestamp(float(str(payload["exp"])), UTC)
        except (UnauthorizatedException, ValueError, OverflowError):
            return
        async with self.uow:
            await self.token_repository.revoke_refresh(token_id, expires_at)

    async def patch_profile(
        self: Self,
        user_id: uuid.UUID,
        update_data: user_schemas.UpdateUserRequest,
    ) -> None:
        if not update_data.model_fields_set:
            return
        async with self.uow:
            await self.update(user_id, update_data.to_update_user())

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
