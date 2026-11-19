from datetime import datetime
import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common import models


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_refresh_revoked(self, token_id: uuid.UUID) -> bool:
        return await self.session.get(models.RevokedRefreshToken, token_id) is not None

    async def revoke_refresh(self, token_id: uuid.UUID, expires_at: datetime) -> None:
        await self.session.execute(
            insert(models.RevokedRefreshToken)
            .values(id=token_id, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=["id"])
        )
