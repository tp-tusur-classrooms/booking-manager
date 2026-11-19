from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Security

from src.api.v1.common import get_current_user, require_admin
import src.domain.users.schemas as user_schemas
import src.domain.users.services as user_services
from src.low.container import Container
from src.low.exceptions import APIException

router = APIRouter()


@router.post(
    path="/users",
    response_model=user_schemas.User,
    status_code=201,
    dependencies=[Security(require_admin)],
    responses={
        400: {"model": APIException},
        401: {"model": APIException},
        403: {"model": APIException},
        409: {"model": APIException},
    },
    tags=["Users"],
)
@inject
async def create_user(
    data: user_schemas.RegisterUserRequest,
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> user_schemas.User:
    """Администратор создаёт пользователя с ролью user, без выдачи токенов."""
    return await user_service.register(data)


@router.get(
    path="/profile",
    response_model=user_schemas.User,
    responses={401: {"model": APIException}},
    tags=["Users"],
)
async def get_profile(
    current_user: user_schemas.User = Security(get_current_user),
) -> user_schemas.User:
    """
    Получение профиля пользователя
    """
    return current_user
