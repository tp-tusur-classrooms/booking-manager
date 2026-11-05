from typing import Self
import uuid

from src.domain.base.base_service import BaseService
from src.domain.security.services import EmailSenderService
from src.domain.token.schemas import TokenType
from src.domain.token.services import VerificationTokenService
import src.domain.users.schemas as user_schemas
from src.domain.users.services import UserService
from src.low.database import UnitOfWork
from src.low.exceptions import DublicateException, UserException


class EmailChangeService(BaseService):
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

    async def request_change(self: Self, user_id: uuid.UUID, new_email: str) -> None:
        existing = await self.user_service.get_by_email_or_none(new_email)
        if existing:
            raise DublicateException("Email уже используется")

        async with self.uow:
            token = await self.token_service.create_token(
                user_id=user_id,
                token_type=TokenType.EMAIL_CHANGE,
                payload={"new_email": new_email},
            )

        await self.email_sender_service.send_email_change_code(new_email, token.code)

    async def confirm_change(self: Self, user_id: uuid.UUID, code: str) -> None:
        async with self.uow:
            token = await self.token_service.verify_and_consume(
                user_id=user_id,
                code=code,
                token_type=TokenType.EMAIL_CHANGE,
                error_msg="Неверный или истёкший код смены email",
            )

            if not token.payload:
                raise UserException("Не удалось определить новый email")
            new_email = token.payload.get("new_email")
            if not new_email:
                raise UserException("Не удалось определить новый email")

            await self.user_service.update(
                user_id,
                user_schemas.UpdateUser(email=new_email, is_email_verified=False),
            )

            verification_token = await self.token_service.create_token(
                user_id=user_id,
                token_type=TokenType.EMAIL_VERIFICATION,
            )

        await self.email_sender_service.send_email_verification_code(
            new_email, verification_token.code
        )
