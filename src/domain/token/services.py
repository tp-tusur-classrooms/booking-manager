from datetime import UTC, datetime, timedelta
import secrets
import string
from typing import Any, Self
import uuid

from src.domain.base.base_service import BaseService
from src.domain.common import models
from src.domain.token.repositories import TokenRepository
import src.domain.token.schemas as token_schemas
from src.low.config.modules import VerificationTokenConfig
from src.low.exceptions import NotFoundException, UserException


class VerificationTokenService(BaseService):
    """
    Универсальный сервис для генерации и проверки кодов подтверждения.
    """

    def __init__(
        self: Self,
        token_repository: TokenRepository,
        token_config: VerificationTokenConfig,
    ) -> None:
        self.token_repository = token_repository
        self.token_config = token_config

    def _to_business(
        self: Self, raw_token: models.VerificationToken
    ) -> token_schemas.Token:
        return token_schemas.Token.model_validate(raw_token, from_attributes=True)

    # Domain
    async def create(
        self: Self, create_token: token_schemas.CreateToken
    ) -> token_schemas.Token:
        raw_token = await self.token_repository.create(create_token)
        return self._to_business(raw_token)

    async def get_first(
        self: Self, filter_token: token_schemas.FilterToken
    ) -> token_schemas.Token:
        raw_token = await self.token_repository.get_first(filter_token)
        return self._to_business(raw_token)

    async def create_token(
        self: Self,
        user_id: uuid.UUID,
        token_type: token_schemas.TokenType,
        payload: dict[str, Any] | None = None,
    ) -> token_schemas.Token:

        await self.token_repository.invalidate_active(user_id, token_type)

        code = self._generate_code(self.token_config.code_length)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=self.token_config.expiry_minutes
        )

        create_token = token_schemas.CreateToken(
            user_id=user_id,
            code=code,
            type=token_type,
            expires_at=expires_at,
            payload=payload,
        )

        return await self.create(create_token)

    async def verify_and_consume(
        self: Self,
        user_id: uuid.UUID,
        code: str,
        token_type: token_schemas.TokenType,
        error_msg: str = "Неверный или истёкший код",
    ) -> token_schemas.Token:

        filters = token_schemas.FilterToken(
            user_id=user_id, code=code, type=token_type, used=False
        )

        try:
            token = await self.get_first(filters)
        except NotFoundException as e:
            raise UserException(error_msg) from e

        if token.is_expired():
            raise UserException(error_msg)

        await self.token_repository.update(
            token.id, token_schemas.UpdateToken(used=True)
        )

        return token

    def _generate_code(self: Self, length: int) -> str:
        if length <= 0:
            raise ValueError(f"Code length must be positive, got {length}")
        characters = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))
