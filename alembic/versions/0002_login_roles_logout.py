"""Авторизация по логину, роли и хранение отозванных токенов обновления.

Идентификатор ревизии: 0002
Предыдущая ревизия: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("login", sa.String(32), nullable=True))
    # UUID задаёт старым аккаунтам уникальные логины, не раскрывая почту.
    op.execute("UPDATE \"user\" SET login = replace(id::text, '-', '')")
    op.alter_column("user", "login", nullable=False)
    op.create_unique_constraint("uq_user_login", "user", ["login"])
    op.create_check_constraint("ck_user_login_lower", "user", "login = lower(login)")
    op.add_column(
        "user", sa.Column("role", sa.String(16), server_default="user", nullable=False)
    )
    op.create_check_constraint("ck_user_role", "user", "role IN ('user', 'admin')")
    op.alter_column("user", "email", existing_type=sa.String(255), nullable=True)
    op.execute(
        "UPDATE \"user\" SET name = 'Пользователь' WHERE name IS NULL OR name = ''"
    )
    op.alter_column("user", "name", existing_type=sa.String(255), nullable=False)
    op.create_table(
        "revoked_refresh_token",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    # Не подменяем почту и не удаляем аккаунты ради ограничения NOT NULL.
    # Перед откатом нужно заполнить почту у аккаунтов, созданных только по логину.
    op.alter_column("user", "email", existing_type=sa.String(255), nullable=False)
    op.drop_table("revoked_refresh_token")
    op.alter_column("user", "name", existing_type=sa.String(255), nullable=True)
    op.drop_constraint("ck_user_role", "user", type_="check")
    op.drop_column("user", "role")
    op.drop_constraint("ck_user_login_lower", "user", type_="check")
    op.drop_constraint("uq_user_login", "user", type_="unique")
    op.drop_column("user", "login")
