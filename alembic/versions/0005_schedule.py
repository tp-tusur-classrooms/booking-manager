"""Teaching period dictionary and dated lessons with overlap protection.

Revision ID: 0005
Revises: 0004
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "teaching_period_template",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.UniqueConstraint("order", name="uq_teaching_period_order"),
        sa.UniqueConstraint("start_time", "end_time", name="uq_teaching_period_times"),
        sa.CheckConstraint('"order" > 0', name="ck_teaching_period_order"),
        sa.CheckConstraint("start_time < end_time", name="ck_teaching_period_times"),
        sa.CheckConstraint(
            "extract(second FROM start_time) = 0 AND extract(second FROM end_time) = 0",
            name="ck_teaching_period_minutes",
        ),
    )
    op.create_table(
        "scheduled_lesson",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("period_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("group", sa.String(200), nullable=True),
        sa.Column("teacher", sa.String(200), nullable=True),
        sa.ForeignKeyConstraint(
            ["room_id"], ["room.id"], name="fk_scheduled_lesson_room"
        ),
        sa.ForeignKeyConstraint(
            ["period_id"],
            ["teaching_period_template.id"],
            name="fk_scheduled_lesson_period",
        ),
        sa.CheckConstraint("starts_at < ends_at", name="ck_scheduled_lesson_times"),
        sa.CheckConstraint(
            "subject = btrim(subject) AND length(subject) > 0",
            name="ck_scheduled_lesson_subject",
        ),
        postgresql.ExcludeConstraint(
            ("room_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            name="ex_scheduled_lesson_overlap",
            using="gist",
        ),
    )
    op.create_index("ix_scheduled_lesson_date", "scheduled_lesson", ["date"])
    op.create_index("ix_scheduled_lesson_period", "scheduled_lesson", ["period_id"])
    # БД, а не только API, связывает фактический интервал с датой и справочником.
    op.execute("""
        CREATE FUNCTION set_scheduled_lesson_times() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE period_row teaching_period_template%ROWTYPE;
        BEGIN
            SELECT * INTO period_row FROM teaching_period_template
                WHERE id = NEW.period_id FOR SHARE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Unknown teaching period'
                    USING ERRCODE = '23503', CONSTRAINT = 'fk_scheduled_lesson_period';
            END IF;
            NEW.starts_at := (NEW.date + period_row.start_time) AT TIME ZONE 'Asia/Tomsk';
            NEW.ends_at := (NEW.date + period_row.end_time) AT TIME ZONE 'Asia/Tomsk';
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER scheduled_lesson_times
        BEFORE INSERT OR UPDATE OF date, period_id, starts_at, ends_at
        ON scheduled_lesson FOR EACH ROW EXECUTE FUNCTION set_scheduled_lesson_times()
    """)
    op.execute("""
        CREATE FUNCTION protect_used_teaching_period() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF (OLD.start_time, OLD.end_time) IS DISTINCT FROM (NEW.start_time, NEW.end_time)
                AND EXISTS (SELECT 1 FROM scheduled_lesson WHERE period_id = OLD.id) THEN
                RAISE EXCEPTION 'Cannot change the times of a period used by lessons'
                    USING ERRCODE = '23514', CONSTRAINT = 'ck_teaching_period_in_use';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER teaching_period_in_use
        BEFORE UPDATE OF start_time, end_time ON teaching_period_template
        FOR EACH ROW EXECUTE FUNCTION protect_used_teaching_period()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER teaching_period_in_use ON teaching_period_template")
    op.execute("DROP FUNCTION protect_used_teaching_period()")
    op.drop_table("scheduled_lesson")
    op.execute("DROP FUNCTION set_scheduled_lesson_times()")
    op.drop_table("teaching_period_template")
    # btree_gist может использоваться другими таблицами: расширение не удаляем.
