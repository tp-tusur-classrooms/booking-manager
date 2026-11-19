"""Создание администратора: uv run --frozen python -m scripts.create_admin."""

import argparse
import asyncio
from getpass import getpass
from pathlib import Path

from pydantic import ValidationError

from src.domain.common.models import User
from src.domain.security.services import HasherService
from src.domain.users.repositories import UserRepository
from src.domain.users.schemas import RegisterUserRequest
from src.low.config.reader import ConfigReader
from src.low.creds.reader import CredsReader
from src.low.database import Database, UnitOfWork
from src.low.exceptions import DublicateException, UserException


async def create_admin(config_dir: Path, request: RegisterUserRequest) -> None:
    request.validate_req()
    data = request.to_create_user()
    data.role = "admin"
    data.password = HasherService().get_password_hash(data.password)
    config = ConfigReader.load(config_dir / "config.json")
    creds = CredsReader.load(config_dir / config.general.creds)
    database = Database(config.modules.database, creds.modules.database)
    try:
        async with database.session_factory() as session, UnitOfWork(session):
            repository = UserRepository(model=User, session=session)
            await repository.create(data)
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Создание администратора вне HTTP API")
    parser.add_argument("--login", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--config-dir", type=Path, default=Path("config/prod"))
    args = parser.parse_args()
    try:
        request = RegisterUserRequest(
            login=args.login,
            name=args.name,
            password=getpass("Пароль: "),
            confirm_password=getpass("Повторите пароль: "),
        )
        asyncio.run(create_admin(args.config_dir, request))
    except ValidationError:
        parser.exit(1, "Проверьте имя, логин и пароль согласно README.md.\n")
    except DublicateException:
        parser.exit(1, "Логин уже занят. Существующая учётная запись не изменена.\n")
    except UserException as exc:
        parser.exit(1, exc.public_message + "\n")
    print("Администратор создан.")


if __name__ == "__main__":
    main()
