"""Удаление почты, связи с аватаром и почтовых кодов подтверждения.

Идентификатор ревизии: 0003
Предыдущая ревизия: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_user_avatar", "user", type_="foreignkey")
    op.drop_constraint("ix_unique_email", "user", type_="unique")
    op.drop_column("user", "avatar_id")
    op.drop_column("user", "is_email_verified")
    op.drop_column("user", "email")
    op.drop_table("verification_tokens")
    sa.Enum(name="token_type_enum").drop(op.get_bind(), checkfirst=False)


def downgrade() -> None:
    # Восстанавливаем структуру, но не удалённые значения и коды подтверждения.
    op.add_column("user", sa.Column("email", sa.String(255), nullable=True))
    op.add_column(
        "user",
        sa.Column(
            "is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.alter_column("user", "is_email_verified", server_default=None)
    op.add_column("user", sa.Column("avatar_id", sa.UUID(), nullable=True))
    op.create_unique_constraint("ix_unique_email", "user", ["email"])
    op.create_foreign_key("fk_user_avatar", "user", "file", ["avatar_id"], ["id"])
    op.create_table(
        "verification_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "PASSWORD_RESET",
                "EMAIL_VERIFICATION",
                "EMAIL_CHANGE",
                name="token_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_verification_tokens_code", "verification_tokens", ["code"])
    op.create_index("ix_verification_tokens_type", "verification_tokens", ["type"])
