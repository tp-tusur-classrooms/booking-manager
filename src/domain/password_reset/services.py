# src/domain/password_reset/services.py

from typing import Self

from src.domain.base.base_service import BaseService
import src.domain.password_reset.schemas as password_reset_schemas
from src.domain.security.services import EmailSenderService
from src.domain.token.schemas import TokenType
from src.domain.token.services import VerificationTokenService
from src.domain.users.services import UserService
from src.low.database import UnitOfWork
from src.low.exceptions import UserException


class PasswordResetService(BaseService):
    def __init__(
        self: Self,
        uow: UnitOfWork,
        token_service: VerificationTokenService,
        user_service: UserService,
        email_sender_service: EmailSenderService,
    ) -> None:
        self.uow = uow
        self.token_service = token_service
        self.user_service = user_service
        self.email_sender_service = email_sender_service

    async def request_password_reset(self: Self, email: str) -> None:
        user = await self.user_service.get_by_email_or_none(email)
        if not user:
            return

        async with self.uow:
            token = await self.token_service.create_token(
                user_id=user.id,
                token_type=TokenType.PASSWORD_RESET,
            )

        await self.email_sender_service.send_password_reset_code(user.email, token.code)

    async def confirm_password_reset(
        self: Self, data: password_reset_schemas.PasswordResetConfirm
    ) -> None:
        if not data.passwords_match():
            raise UserException("Пароли должны совпадать")

        user = await self.user_service.get_by_email_or_none(data.email)
        if not user:
            raise UserException("Пользователя не существует")

        async with self.uow:
            await self.token_service.verify_and_consume(
                user_id=user.id, code=data.code, token_type=TokenType.PASSWORD_RESET
            )

            await self.user_service.set_password(user.id, data.new_password)
