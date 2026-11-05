import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Security

from src.api.v1.common import (
    get_current_user_id_no_email,
)
from src.domain.base.schemas import Success
import src.domain.email_verification.schemas as email_verification_schemas
import src.domain.password_reset.schemas as password_reset_schemas
import src.domain.password_reset.services as password_reset_services
import src.domain.security.services as security_services
import src.domain.users.schemas as user_schemas
import src.domain.users.services as user_services
from src.low.container import Container

router = APIRouter()


@router.post(
    path="/auth/register",
    response_model=user_schemas.SignedUserResponce,
    tags=["Auth"],
)
@inject
async def register(
    register_user_req: user_schemas.RegisterUserRequest,
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> user_schemas.SignedUserResponce:
    """
    Выполняется регистрация нового пользователя

    Пользователь создается с указанной почтой и паролем. name и avatar = null
    Новый пользователь помечается как не верифицироанный, отправляется письмо с кодом на
    почту
    """

    register_user_req.validate_req()

    return await user_service.register(register_user_req)


@router.post(
    path="/auth/login",
    response_model=user_schemas.SignedUserResponce,
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
    path="/auth/forgot-password",
    response_model=Success,
    tags=["Auth"],
)
@inject
async def forgot_password(
    data: password_reset_schemas.PasswordResetRequest,
    password_reset_service: password_reset_services.PasswordResetService = Depends(
        Provide[Container.password_reset_service]
    ),
) -> Success:
    """
    Запрос на восстановление пароля (отправка кода на email)
    """
    await password_reset_service.request_password_reset(data.email)

    return Success()


@router.post(
    path="/auth/reset-password",
    response_model=Success,
    tags=["Auth"],
)
@inject
async def reset_password(
    data: password_reset_schemas.PasswordResetConfirm,
    password_reset_service: password_reset_services.PasswordResetService = Depends(
        Provide[Container.password_reset_service]
    ),
) -> Success:
    """
    Подтверждение кода восстановления и установка нового пароля
    """
    await password_reset_service.confirm_password_reset(data)

    return Success()


@router.post(
    path="/auth/refresh",
    response_model=user_schemas.RefreshedTokenResponse,
    tags=["Auth"],
)
@inject
async def refresh_token(
    data: user_schemas.RefreshTokenRequest,
    token_service: security_services.TokenService = Depends(
        Provide[Container.token_service]
    ),
) -> user_schemas.RefreshedTokenResponse:
    """
    По refresh токену получает новый access токен для пользователя
    """
    user_id = token_service.get_user_id_from_refresh_token(data.refresh_token)

    token = token_service.create_access_token({"sub": str(user_id)})

    return user_schemas.RefreshedTokenResponse(token=token)


@router.post(
    path="/auth/confirm-email",
    response_model=Success,
    tags=["Auth"],
)
@inject
async def confirm_email(
    data: email_verification_schemas.ConfirmEmailVerification,
    user_id: uuid.UUID = Security(get_current_user_id_no_email),
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> Success:
    """
    Подтвердить почту при помощи кода из письма,
    ожидает указанного jwt токена, но не проверяет на валидность почты
    """
    await user_service.verify_email(user_id, data.code)

    return Success()
