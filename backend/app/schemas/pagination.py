from typing import Generic, List, TypeVar
from pydantic.generics import GenericModel
from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class Paginated(GenericModel, Generic[T]):
    items: List[T]
    meta: PageMeta

    model_config = {"from_attributes": True}
