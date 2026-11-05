import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Form, Request, Security, UploadFile

from src.api.v1.common import collect_patch_form, get_current_user_id
from src.domain.base.schemas import Success
import src.domain.email_change.schemas as email_change_schemas
import src.domain.email_change.services as email_change_services
import src.domain.users.schemas as user_schemas
import src.domain.users.services as user_services
from src.low.container import Container

router = APIRouter()


@router.get(
    path="/profile",
    response_model=user_schemas.User,
    tags=["Users"],
)
@inject
async def get_profile(
    user_id: uuid.UUID = Security(get_current_user_id),
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> user_schemas.User:
    """
    Получение профиля пользователя
    """
    return await user_service.get_by_id(user_id)


@router.post(
    path="/profile/change-password",
    response_model=Success,
    tags=["Users"],
)
@inject
async def change_password(
    update_data: user_schemas.UpdatePasswordRequest,
    user_id: uuid.UUID = Security(get_current_user_id),
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> Success:
    """
    Изменение пароля авторизованного пользователя
    """
    await user_service.update_password(user_id, update_data)

    return Success()


@router.patch(
    path="/profile",
    response_model=Success,
    tags=["Users"],
)
@inject
async def update_profile(
    request: Request,
    name: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    user_id: uuid.UUID = Security(get_current_user_id),
    user_service: user_services.UserService = Depends(Provide[Container.user_service]),
) -> Success:
    """
    Patch на обновление пользователя.

    Если поле не задано - оно не изменится, если оно null - на базе тоже будет null
    """
    update_request = await collect_patch_form(request, user_schemas.UpdateUserRequest)
    form = await request.form()
    clear_avatar = "avatar" in form and avatar is None
    await user_service.patch_profile(user_id, update_request, avatar, clear_avatar)
    return Success()


@router.post(
    path="/profile/change-email",
    response_model=Success,
    tags=["Users"],
)
@inject
async def change_email(
    data: email_change_schemas.EmailChangeRequest,
    user_id: uuid.UUID = Security(get_current_user_id),
    email_change_service: email_change_services.EmailChangeService = Depends(
        Provide[Container.email_change_service]
    ),
) -> Success:
    """
    Сменить почту авторизованному пользователю. Отправит письмо с кодом на почту
    """

    await email_change_service.request_change(user_id, str(data.new_email))
    return Success()


@router.post(
    path="/profile/confirm-email-change",
    response_model=Success,
    tags=["Users"],
)
@inject
async def confirm_email_change(
    data: email_change_schemas.EmailChangeConfirm,
    user_id: uuid.UUID = Security(get_current_user_id),
    email_change_service: email_change_services.EmailChangeService = Depends(
        Provide[Container.email_change_service]
    ),
) -> Success:
    """
    Подтверждение изменения почты по коду для авторизованного пользователя
    """

    await email_change_service.confirm_change(user_id, data.code)
    return Success()
