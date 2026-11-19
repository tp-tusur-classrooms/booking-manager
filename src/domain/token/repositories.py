from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

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
    async def is_refresh_revoked(self, token_id: uuid.UUID) -> bool:
        return await self.session.get(models.RevokedRefreshToken, token_id) is not None

    async def revoke_refresh(self, token_id: uuid.UUID, expires_at: datetime) -> None:
        await self.session.execute(
            insert(models.RevokedRefreshToken)
            .values(id=token_id, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=["id"])
        )

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
