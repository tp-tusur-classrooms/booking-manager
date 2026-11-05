import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import src.domain.security.services as security_services
import src.domain.users.services as user_services
from src.low.container import Container
from src.low.exceptions import EmailUnverifiedException, UnauthorizatedException

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
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
    token_service: security_services.TokenService = Depends(
        Provide[Container.token_service]
    ),
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> uuid.UUID:
    """
    Производит получение user_id из jwt токена, а также
    проверяет что пользователь подтвердил email

    Может выбросить ошибку если:
    1. Не было jwt токена или он был в корне неверным
    2. Использованный токен устарел
    3. Email не был подтвержден пользователем
    """
    if not credentials:
        raise UnauthorizatedException

    token = credentials.credentials
    user_id = token_service.get_user_id_from_token(token)

    user = await user_service.get_full_by_id(user_id)
    if not user.is_email_verified:
        raise EmailUnverifiedException

    return user_id


@inject
async def get_current_user_id_no_email(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
    token_service: security_services.TokenService = Depends(
        Provide[Container.token_service]
    ),
) -> uuid.UUID:
    """
    Производит получение user_id из jwt токена

    Может выбросить ошибку если:
    1. Не было jwt токена или он был в корне неверным
    2. Использованный токен устарел
    """
    if not credentials:
        raise UnauthorizatedException

    token = credentials.credentials
    user_id = token_service.get_user_id_from_token(token)

    return user_id
