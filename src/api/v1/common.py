import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.domain.users.schemas import User
import src.domain.users.services as user_services
from src.low.container import Container
from src.low.exceptions import (
    ForbiddenException,
    UnauthorizatedException,
)

bearer = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


async def collect_patch_form[T: BaseModel](request: Request, schema_cls: type[T]) -> T:
    form = await request.form()
    data: dict = {}
    for field_name in schema_cls.model_fields:
        if field_name in form:
            value = form[field_name]
            if isinstance(value, str):
                data[field_name] = value if value != "" else None
    return schema_cls.model_validate(data)


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> User:
    """Проверяет токен доступа и загружает текущего пользователя и его роль из БД."""
    if not credentials:
        raise UnauthorizatedException("Требуется вход в систему", "not_authenticated")
    return await user_service.get_by_token(credentials.credentials)


async def get_current_user_id(
    current_user: User = Security(get_current_user),
) -> uuid.UUID:
    return current_user.id


get_current_user_id_no_email = get_current_user_id


async def require_admin(current_user: User = Security(get_current_user)) -> User:
    """Подключается через Security(require_admin) к административным методам.

    Для проверки прав нельзя доверять параметрам запроса или полю role в JWT.
    """
    if current_user.role != "admin":
        raise ForbiddenException
    return current_user
