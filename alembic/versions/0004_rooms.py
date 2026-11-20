"""Rooms, reference dictionaries and equipment links.

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("building", "equipment"):
        op.create_table(
            table,
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, unique=True),
        )
    op.create_table(
        "room",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column(
            "building_id", sa.UUID(), sa.ForeignKey("building.id"), nullable=False
        ),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("photo_id", sa.UUID(), sa.ForeignKey("file.id"), nullable=True),
        sa.CheckConstraint(
            "number = btrim(number) AND length(number) > 0", name="ck_room_number"
        ),
        sa.CheckConstraint("capacity BETWEEN 1 AND 1000", name="ck_room_capacity"),
        sa.CheckConstraint("floor BETWEEN -5 AND 50", name="ck_room_floor"),
    )
    op.create_index(
        "uq_room_building_number",
        "room",
        ["building_id", sa.text('lower(number COLLATE "pg_unicode_fast")')],
        unique=True,
    )
    op.create_table(
        "room_equipment",
        sa.Column(
            "room_id",
            sa.UUID(),
            sa.ForeignKey("room.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "equipment_id", sa.UUID(), sa.ForeignKey("equipment.id"), primary_key=True
        ),
    )


def downgrade() -> None:
    op.drop_table("room_equipment")
    op.drop_index("uq_room_building_number", table_name="room")
    op.drop_table("room")
    op.drop_table("equipment")
    op.drop_table("building")
