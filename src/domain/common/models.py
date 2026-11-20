from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now


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

    login: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    role: Mapped[str] = mapped_column(
        sa.String(16), default="user", server_default="user"
    )
    password: Mapped[str] = mapped_column(sa.String(255))
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("login", name="uq_user_login"),
        sa.CheckConstraint("login = lower(login)", name="ck_user_login_lower"),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_user_role"),
    )


class RevokedRefreshToken(Base):
    __tablename__ = "revoked_refresh_token"

    # В id хранится идентификатор jti из JWT, а не сам токен.
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))


class Building(Base):
    __tablename__ = "building"

    name: Mapped[str] = mapped_column(sa.String(255), unique=True)


class Equipment(Base):
    __tablename__ = "equipment"

    name: Mapped[str] = mapped_column(sa.String(255), unique=True)


room_equipment = sa.Table(
    "room_equipment",
    Base.metadata,
    sa.Column(
        "room_id", sa.ForeignKey("room.id", ondelete="CASCADE"), primary_key=True
    ),
    sa.Column("equipment_id", sa.ForeignKey("equipment.id"), primary_key=True),
)


class Room(Base, AuditMixin):
    __tablename__ = "room"

    number: Mapped[str] = mapped_column(sa.String(20))
    building_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("building.id"))
    floor: Mapped[int]
    capacity: Mapped[int]
    description: Mapped[str | None] = mapped_column(sa.String(1000))
    photo_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("file.id"))

    building: Mapped[Building] = relationship(lazy="raise")
    equipment: Mapped[list[Equipment]] = relationship(
        secondary=room_equipment, order_by=Equipment.name, lazy="raise"
    )
    photo: Mapped[File | None] = relationship(lazy="raise")

    __table_args__ = (
        sa.Index(
            "uq_room_building_number",
            building_id,
            sa.func.lower(number.collate("pg_unicode_fast")),
            unique=True,
        ),
        sa.CheckConstraint(
            "number = btrim(number) AND length(number) > 0", name="ck_room_number"
        ),
        sa.CheckConstraint("capacity BETWEEN 1 AND 1000", name="ck_room_capacity"),
        sa.CheckConstraint("floor BETWEEN -5 AND 50", name="ck_room_floor"),
    )
