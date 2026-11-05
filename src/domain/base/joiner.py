from typing import Self

from pydantic import BaseModel
from sqlalchemy.orm.strategy_options import Load


class WithSchema(BaseModel):
    """
    Некая pydantic схема которая отражает присоединяемые поля, с lazy=selectin
    Может работать в вложенностью

    Схема имеет следующую логику:
    class someWith(WithSchema):
        other: bool = False
        nested: Option[WithSchema] = None

    В данной логике, если other = True, то он окажется в selectin, иначе нет
    Если nested будет none, то он не будет в selectin, однако если это будет
    инстанс WithSchema, то он будет загружен, согласно полям
    """

    def collect_selectins(self: Self, model: type) -> list[Load]:
        """Build SQLAlchemy selectinload options in one function"""

        options: list[Load] = []

        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, WithSchema):
                nested_options = value.collect_selectins(
                    getattr(model, field_name).property.mapper.class_
                )
                options.append(
                    Load(model)
                    .selectinload(getattr(model, field_name))
                    .options(*nested_options)
                )
            elif isinstance(value, bool) and value:
                options.append(Load(model).selectinload(getattr(model, field_name)))

        return options
