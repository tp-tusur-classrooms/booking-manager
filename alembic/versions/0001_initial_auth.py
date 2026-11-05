"""Initial users, avatars and verification tokens.

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "user",
        *audit_columns(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("avatar_id", sa.UUID(), nullable=True),
        sa.UniqueConstraint("email", name="ix_unique_email"),
    )
    op.create_table(
        "file",
        *audit_columns(),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("sub_folder", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("stored_filename", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
    )
    op.create_foreign_key("fk_user_avatar", "user", "file", ["avatar_id"], ["id"])
    op.create_table(
        "verification_tokens",
        *audit_columns(),
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


def downgrade() -> None:
    op.drop_table("verification_tokens")
    sa.Enum(name="token_type_enum").drop(op.get_bind(), checkfirst=False)
    op.drop_constraint("fk_user_avatar", "user", type_="foreignkey")
    op.drop_table("file")
    op.drop_table("user")
