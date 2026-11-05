from datetime import datetime
from typing import Any
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from src.domain.token.schemas import TokenType


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=now(), onupdate=now()
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(sa.Boolean, default=False)


class File(Base, AuditMixin):
    __tablename__ = "file"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("user.id")
    )
    sub_folder: Mapped[str]
    original_filename: Mapped[str]
    stored_filename: Mapped[str]
    size: Mapped[int]


class User(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(sa.String(255))
    password: Mapped[str] = mapped_column(sa.String(255))
    name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    is_email_verified: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    avatar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("file.id", name="fk_user_avatar", use_alter=True),
        nullable=True,
    )
    avatar = relationship(
        "File", lazy="selectin", uselist=False, foreign_keys=[avatar_id]
    )

    __table_args__ = (sa.UniqueConstraint("email", name="ix_unique_email"),)


class VerificationToken(Base, AuditMixin):
    __tablename__ = "verification_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("user.id")
    )
    code: Mapped[str] = mapped_column(sa.String(50), index=True)
    type: Mapped[str] = mapped_column(
        sa.Enum(TokenType, name="token_type_enum"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
