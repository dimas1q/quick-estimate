from pydantic import BaseModel, Field
from typing import Any, List, Optional


class TemplateItemBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit: str
    internal_price: float = Field(..., gt=0)
    external_price: float = Field(..., gt=0)
    category: Optional[str] = None


class TemplateItemCreate(TemplateItemBase):
    pass


class TemplateItemOut(TemplateItemBase):
    id: int

    model_config = {"from_attributes": True}


class EstimateTemplateBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    use_internal_price: bool = True


class EstimateTemplateCreate(EstimateTemplateBase):
    items: List[TemplateItemCreate]


class EstimateTemplateUpdate(EstimateTemplateBase):
    items: List[TemplateItemCreate]


class EstimateTemplateOut(EstimateTemplateBase):
    id: int
    items: List[TemplateItemOut]
    use_internal_price: bool = True

    model_config = {"from_attributes": True}


class TemplateImportError(BaseModel):
    path: str
    message: str


class TemplateImportSummary(BaseModel):
    name: str
    item_count: int
    category_count: int
    categories: List[str]
    name_exists: bool


class TemplateImportPreviewOut(BaseModel):
    valid: bool
    errors: List[TemplateImportError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    preview: Optional[EstimateTemplateCreate] = None
    summary: Optional[TemplateImportSummary] = None


class TemplateImportRequest(BaseModel):
    payload: dict[str, Any]
