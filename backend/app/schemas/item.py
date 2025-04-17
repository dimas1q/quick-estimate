from pydantic import BaseModel, Field


class EstimateItemBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    quantity: float = Field(..., gt=0)
    unit: str
    unit_price: float = Field(..., gt=0)
    category: str = ""


class EstimateItemCreate(EstimateItemBase):
    pass


class EstimateItemOut(EstimateItemBase):
    id: int

    model_config = {"from_attributes": True}
