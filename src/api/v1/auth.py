from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response

import src.domain.users.schemas as user_schemas
import src.domain.users.services as user_services
from src.low.container import Container
from src.low.exceptions import APIException

router = APIRouter()


@router.post(
    path="/auth/login",
    response_model=user_schemas.SignedUserResponce,
    responses={400: {"model": APIException}, 401: {"model": APIException}},
    tags=["Auth"],
)
@inject
async def login(
    data: user_schemas.LoginUserRequest,
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> user_schemas.SignedUserResponce:
    """
    Вход пользователя в систему
    """
    return await user_service.login(data)


@router.post(
    path="/auth/refresh",
    response_model=user_schemas.RefreshedTokenResponse,
    responses={400: {"model": APIException}, 401: {"model": APIException}},
    tags=["Auth"],
)
@inject
async def refresh_token(
    data: user_schemas.RefreshTokenRequest,
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> user_schemas.RefreshedTokenResponse:
    """
    Выдаёт токен доступа по действующему токену обновления и существующему аккаунту.
    Неверный, истёкший или отозванный токен обновления: 401 invalid_refresh_token.
    """
    return await user_service.refresh(data.refresh_token)


@router.post(
    path="/auth/logout",
    status_code=204,
    tags=["Auth"],
    responses={400: {"model": APIException}},
)
@inject
async def logout(
    data: user_schemas.RefreshTokenRequest,
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> Response:
    """Отзывает токен обновления в БД. Повторный, неверный или истёкший токен: 204.

    Токен доступа не требуется и действует до exp. Клиент удаляет оба токена.
    """
    await user_service.logout(data.refresh_token)
    return Response(status_code=204)
