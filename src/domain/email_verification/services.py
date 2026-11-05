from typing import Self
import uuid

from src.domain.base.base_service import BaseService
from src.domain.security.services import EmailSenderService
from src.domain.token.schemas import TokenType
from src.domain.token.services import VerificationTokenService


class EmailVerificationService(BaseService):
    def __init__(
        self: Self,
        token_service: VerificationTokenService,
        email_sender_service: EmailSenderService,
    ) -> None:
        self.token_service = token_service
        self.email_sender_service = email_sender_service

    # Domain
    async def create_challenge(self: Self, user_id: uuid.UUID, email: str) -> None:
        token = await self.token_service.create_token(
            user_id=user_id, token_type=TokenType.EMAIL_VERIFICATION
        )
        await self.email_sender_service.send_email_verification_code(email, token.code)

    async def verify_email(self: Self, user_id: uuid.UUID, code: str) -> None:
        await self.token_service.verify_and_consume(
            user_id=user_id,
            code=code,
            token_type=TokenType.EMAIL_VERIFICATION,
            error_msg="Неверный или истёкший код верификации",
        )
