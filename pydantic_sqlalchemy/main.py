from typing import Container, Optional, Type

from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


class OrmConfig(BaseConfig):
    orm_mode = True


def sqlalchemy_to_pydantic(
    db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = [], model_name: str = None, base_model: Type[BaseModel] = None
) -> Type[BaseModel]:
    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if not isinstance(attr, ColumnProperty):
            continue
        if not attr.columns:
            continue

        name = attr.key
        if name in exclude:
            continue

        column = attr.columns[0]
        python_type: Optional[type] = None
        if hasattr(column.type, "impl"):
            if hasattr(column.type.impl, "python_type"):
                python_type = column.type.impl.python_type
        elif hasattr(column.type, "python_type"):
            python_type = column.type.python_type
        assert python_type, f"Could not infer python_type for {column}"
        default = None
        if column.default is None and not column.nullable:
            default = ...
        fields[name] = (python_type, default)

    model_name = model_name or db_model.__name__
    if base_model:
        return create_model(model_name, __base__=base_model, **fields)
    return create_model(model_name, __config__=config, **fields)

