from dependency_injector import containers, providers
from dependency_injector.providers import Object

from src.domain.common import models
from src.domain.file.repositories import FileMetadataRepository, FileRepository
from src.domain.file.services import ImageFileService
from src.domain.rooms.repositories import RoomRepository
from src.domain.rooms.services import RoomService
from src.domain.security.services import HasherService, TokenService
from src.domain.token.repositories import TokenRepository
from src.domain.users.repositories import UserRepository
from src.domain.users.services import UserService
from src.low.config.modules import ModulesConfig
from src.low.creds.modules import ModulesCreds
from src.low.database import Database, UnitOfWork


class Container(containers.DeclarativeContainer):
    """
    DI контейнер для всех сервисов и репозиториев приложения.

    Управляет жизненным циклом компонентов и обеспечивает
    их внедрение в маршруты и сервисы.

    Singletons - одна общая инстанция на все приложение
    Factories - новая инстанция при каждом запросе
    """

    # СЛОЙ 1: Инфраструктурные сервисы
    config: Object[ModulesConfig] = providers.Object(object)  # type: ignore
    creds: Object[ModulesCreds] = providers.Object(object)  # type: ignore
    db = providers.Singleton(
        Database, config=config.provided.database, creds=creds.provided.database
    )

    session = providers.ContextLocalSingleton(
        lambda f: f(), db.provided.session_factory
    )
    uow = providers.Factory(UnitOfWork, session=session)

    hasher_service = providers.Singleton(HasherService)

    token_service = providers.Singleton(
        TokenService,
        secret_key=creds.provided.token.secret_key,
        algorithm=config.provided.token.algorithm,
        access_token_expire_minutes=config.provided.token.access_token_expire_min,
        refresh_token_expire_days=config.provided.token.refresh_token_expire_days,
    )

    # СЛОЙ 2: Репозитории
    user_repository = providers.Factory(
        UserRepository,
        model=models.User,
        session=session,
    )

    token_repository = providers.Factory(
        TokenRepository,
        session=session,
    )

    file_repository = providers.Singleton(
        FileRepository, base_folder=config.provided.files.public_path
    )

    file_metadata_repository = providers.Factory(
        FileMetadataRepository,
        model=models.File,
        session=session,
    )

    # СЛОЙ 3: Сервисы домена
    room_repository = providers.Factory(RoomRepository, session=session)
    room_service = providers.Factory(
        RoomService,
        uow=uow,
        room_repository=room_repository,
        file_repository=file_repository,
        public_url=config.provided.files.public_url,
    )

    image_file_service = providers.Factory(
        ImageFileService,
        public_url=config.provided.files.public_url,
        file_metadata_repository=file_metadata_repository,
        file_repository=file_repository,
        sub_folder="images",
    )

    user_service = providers.Factory(
        UserService,
        uow=uow,
        user_repository=user_repository,
        hasher_service=hasher_service,
        token_service=token_service,
        token_repository=token_repository,
    )


# Глобальный контейнер
container: Container = Container()


async def setup_container(config: ModulesConfig, creds: ModulesCreds) -> None:
    """
    Функция для настройки глобального контейнера.

    Аргументы:
        config: ConfigReader объект с настройками приложения
        creds: CredsReader объект с учетными данными
    """
    container.config.override(config)
    container.creds.override(creds)
    container.wire(
        [
            "src.api.v1.auth",
            "src.api.v1.user",
            "src.api.v1.common",
            "src.api.v1.rooms",
        ]
    )
