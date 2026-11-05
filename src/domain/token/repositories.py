import uuid

import sqlalchemy as sa

from src.domain.base.base_repository import BaseRepository
from src.domain.base.joiner import WithSchema
from src.domain.common import models
import src.domain.token.schemas as token_schemas


class TokenRepository(
    BaseRepository[
        models.VerificationToken,
        token_schemas.CreateToken,
        token_schemas.UpdateToken,
        token_schemas.FilterToken,
        WithSchema,
    ]
):
    async def invalidate_active(
        self,
        user_id: uuid.UUID,
        token_type: token_schemas.TokenType,
    ) -> None:
        query = (
            sa.update(models.VerificationToken)
            .where(
                models.VerificationToken.user_id == user_id,
                models.VerificationToken.type == token_type,
                models.VerificationToken.used == False,  # noqa: E712
            )
            .values(used=True)
        )
        await self.session.execute(query)
        await self.session.flush()
