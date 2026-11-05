from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Self, cast
import uuid

from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.base.joiner import WithSchema
from src.domain.base.schemas import OrderBy
from src.domain.common import models
from src.low.exceptions import DublicateException, NotFoundException, ServerException

if TYPE_CHECKING:
    from sqlalchemy.orm import InstrumentedAttribute


class BaseRepository[
    ModelType: models.Base,
    CreateSchemaType: BaseModel,
    UpdateSchemaType: BaseModel,
    FilterSchemaType: BaseModel,
    WithSchemaType: WithSchema,
]:
    """
    Базовый класс для некого репозитория

    Репозиторий в проекте - это некая таблица (или прочее хранилище), с которой можно
    взаимодействовать в формате CRUD

    Все другие репозитории будут наследоваться от BaseRepository,
    по необходимости перегружая функции (которые основаны на Generic),
    и добавляя свои для особенного поведения
    """

    def __init__(
        self: Self,
        model: type[ModelType],
        session: AsyncSession,
    ) -> None:
        self.model: type[ModelType] = model
        self.session: AsyncSession = session

    async def get_or_none(
        self: Self,
        id: uuid.UUID,
        ignore_soft_delete: bool = False,
        with_schema: WithSchemaType | None = None,
    ) -> ModelType | None:
        """
        Получает 1 элемент из репозитория. В случае если элемент не найден,
        будет возвращен None

        Если используется SoftDeleteMixin, и элемент удален, то также вернется None
        Если ignore_soft_delete = True, будет загружено независимо от is_deleted
        selectins - список relationship-атрибутов для явной selectin-загрузки
        """

        query: Any

        if issubclass(self.model, models.SoftDeleteMixin) and not ignore_soft_delete:
            query = sa.select(self.model).where(
                self.model.id == id,
                self.model.is_deleted == False,  # noqa: E712
            )
        else:
            query = sa.select(self.model).where(self.model.id == id)

        if with_schema:
            query = query.options(*with_schema.collect_selectins(self.model))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get(
        self: Self,
        id: uuid.UUID,
        ignore_soft_delete: bool = False,
        with_schema: WithSchemaType | None = None,
    ) -> ModelType:
        """
        Получает 1 элемент из репозитория. В случае если элемент не найден,
        будет выброшена ошибка NotFoundException

        Если используется SoftDeleteMixin, и элемент удален, то также
        выбросится NotFoundException
        Если ignore_soft_delete = True, будет загружено независимо от is_deleted
        selectins - список relationship-атрибутов для явной selectin-загрузки
        """

        obj = await self.get_or_none(
            id, ignore_soft_delete=ignore_soft_delete, with_schema=with_schema
        )

        if obj is None:
            raise NotFoundException(f"{self.model.__name__} not found")

        return obj

    async def get_many(
        self: Self,
        filters: FilterSchemaType | None = None,
        order: OrderBy | None = None,
        with_schema: WithSchemaType | None = None,
    ) -> list[ModelType]:
        """Загрузить несколько с фильтром и соритровкой"""

        query = self._select(filters, order)

        if with_schema:
            query = query.options(*with_schema.collect_selectins(self.model))

        result = await self.session.execute(query)
        return cast("list[ModelType]", result.scalars().all())

    async def count_many(
        self: Self,
        filters: FilterSchemaType | None = None,
    ) -> int:
        subq = self._select(filters).subquery()
        result = await self.session.execute(
            sa.select(sa.func.count()).select_from(subq)
        )
        return result.scalar_one()

    async def get_many_cursor(
        self: Self,
        cursor: str | None = None,
        size: int = 20,
        filters: FilterSchemaType | None = None,
        order: OrderBy | None = None,
        with_schema: WithSchemaType | None = None,
    ) -> CursorPage[ModelType]:
        """Загрузить несколько с фильтром и сортировкой по курсору"""

        query = self._select(filters, order)

        if with_schema:
            query = query.options(*with_schema.collect_selectins(self.model))

        params = CursorParams(cursor=cursor, size=size)

        page: CursorPage[ModelType] = await apaginate(self.session, query, params)
        return page

    async def get_first(
        self: Self,
        filters: FilterSchemaType | None = None,
        order: OrderBy | None = None,
        with_schema: WithSchemaType | None = None,
    ) -> ModelType:
        """Загрузить первый с фильтром"""

        query = self._select(filters, order).limit(1)

        if with_schema:
            query = query.options(*with_schema.collect_selectins(self.model))

        result = await self.session.execute(query)
        obj: ModelType | None = result.scalar_one_or_none()

        if obj is None:
            raise NotFoundException(f"{self.model.__name__} not found")
        return obj

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Создать новую записть"""

        obj_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()

        db_obj: ModelType = self.model(**obj_data)

        self.session.add(db_obj)
        try:
            await self.session.flush()
        except Exception as e:
            if "duplicate" in str(e).lower():
                raise DublicateException(f"{self.model.__name__} already exists") from e
            raise

        return db_obj

    async def update(self, id: uuid.UUID, obj_in: UpdateSchemaType) -> ModelType | None:
        """Обновить запись"""

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        query = (
            sa.update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )

        result = await self.session.execute(query)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: uuid.UUID, hard: bool = False) -> ModelType | None:
        """
        Удалить запись

        По умолчанию пытается удалить запись мягко. Если это не желательное
        поведение, следует установить hard=True

        Если попытаться удалить записть, которая не поддреживает SoftDeleteMixin,
        то будет возвращена ошибка
        """

        if not (issubclass(self.model, models.SoftDeleteMixin) or hard):
            raise ServerException(
                f"Unable to soft-detele {self.model.__name__} because it does"
                + " not inherit from SoftDeleteMixin"
            )

        if hard:
            # Хард удаление записи
            query = (
                sa.delete(self.model).where(self.model.id == id).returning(self.model)
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        else:
            # Софт удаление записи
            # Для этого выполняется get, после чего происходит update
            db_obj: ModelType = await self.get(id=id)
            if db_obj:
                db_obj.is_deleted = True  # ty:ignore[invalid-assignment]
                db_obj.updated_at = sa.func.now()  # ty:ignore[invalid-assignment]
                self.session.add(db_obj)
                await self.session.flush()

            return db_obj

    async def exists(self, id: uuid.UUID) -> bool:
        """Проверить, существует ли такая запись"""

        query = sa.select(self.model.id).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.first() is not None

    def _select(
        self: Self,
        filters: FilterSchemaType | None = None,
        order: OrderBy | None = None,
    ) -> sa.Select[ModelType]:
        """Собрать select query"""

        query = sa.select(self.model)
        if filters:
            query = self._apply_filters(query, filters)

        if order:
            query = self._apply_order(query, order)

        return query

    def _apply_filters(
        self: Self, query: Any, filters: FilterSchemaType, include_deleted: bool = False
    ) -> Any:
        """Примерить фильтры к запросу"""

        filter_clause: list[Any] = []

        # Распаковывем фильтры из FilterSchemaType через model_dump(чтобы получить dict)
        for filter_field_name, filter_field_value in filters.model_dump().items():
            # Скипаем фильтры с None
            if filter_field_value is None:
                continue

            # Получаем атрибут модели по имени поля фильтра.
            model_attr: InstrumentedAttribute[Any] | None = getattr(
                self.model, filter_field_name, None
            )

            # Проверяем, что атрибут модели существует. Если нет, выбрасываем ошибку
            if model_attr is None:
                raise ServerException(
                    f"Model {self.model} does not have attributes {filter_field_name}"
                )

            model_is_array = isinstance(getattr(model_attr, "type", None), ARRAY)
            filter_is_list = isinstance(
                filter_field_value, Sequence
            ) and not isinstance(filter_field_value, (str, bytes))

            if model_is_array and filter_is_list:
                # Если атрибут модели - это массив, и
                # значение фильтра - это список,
                # то используем оператор contains для проверки пересечения
                # Т.е. если в модели массив [1, 2, 3], а в фильтре список
                # [2, 4], то условие будет истинно, так как есть пересечение (2)
                # Эквиавлентно SQL: WHERE model_attr && filter_field_value (оператор
                # пересечения массивов в Postgres)

                filter_clause.append(model_attr.contains(filter_field_value))
            elif model_is_array and not filter_is_list:
                # Если атрибут модели - это массив,
                # а значение фильтра - это одиночное значение,
                # то также используем оператор contains,
                # но оборачиваем значение фильтра в список
                # Т.е. если в модели массив [1, 2, 3], а в фильтре одиночное значение 2,
                # то условие будет истинно, так как есть пересечение (2)

                filter_clause.append(model_attr.contains([filter_field_value]))
            elif not model_is_array and filter_is_list:
                # Если атрибут модели - это одиночное значение,
                # а значение фильтра - это список,
                # то используем оператор in для проверки вхождения
                # Т.е. если в модели значение 2, а в фильтре список [2, 4], то условие
                # будет истинно, так как 2 входит в список
                # SQL: WHERE model_attr IN (filter_field_value)

                filter_clause.append(model_attr.in_(filter_field_value))
            else:
                # В остальных случаях используем оператор равенства

                filter_clause.append(model_attr == filter_field_value)

        # По умолчанию исключаем мягко удалённые записи (is_deleted == True)
        # Опционально можно загрузить все записи, передав include_deleted=True
        if not include_deleted and hasattr(self.model, "is_deleted"):
            filter_clause.append(self.model.is_deleted == False)  # noqa: E712

        query = query.filter(*filter_clause)
        return query

    def _apply_order(self: Self, query: Any, order: OrderBy) -> Any:
        """Применить сортировку к запросу"""

        clauses = []
        for clause in order.clauses:
            clauses.append(clause.direction._sort_function()(clause.field))

        id_in_model = bool(self.model.id)
        id_in_order = "id" in [el.field for el in order.clauses]

        # Добавляем первичный ключ последним как tie-breaker
        if not id_in_order and id_in_model:
            clauses.append(sa.asc(self.model.id))

        query = query.order_by(*clauses)
        return query
