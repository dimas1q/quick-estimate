from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.estimate import EstimateStatus


class GranularityEnum(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"


class TimeSeriesItem(BaseModel):
    period: str  # напр. "2025-05" или "2025-Q2"
    value: float


class ServiceMetric(BaseModel):
    name: str  # название услуги или клиента
    total_amount: float  # сумма выручки


class ResponsibleMetric(BaseModel):
    name: str  # имя ответственного
    estimates_count: int  # число смет
    total_amount: float  # сумма выручки


class ClientAnalytics(BaseModel):
    client_id: int
    total_estimates: int
    total_amount: float
    average_amount: float
    timeseries: List[TimeSeriesItem]
    by_responsible: List[ResponsibleMetric]
    top_services: List[ServiceMetric]
    granularity: GranularityEnum
    median_amount: float
    mom_growth: Optional[float]
    yoy_growth: Optional[float]


class GlobalAnalytics(BaseModel):
    total_estimates: int
    total_amount: float
    average_amount: float
    timeseries: List[TimeSeriesItem]
    top_clients: List[ServiceMetric]
    by_responsible: List[ResponsibleMetric]
    top_services: List[ServiceMetric]
    granularity: GranularityEnum
    median_amount: float
    arpu: float
    mom_growth: Optional[float]
    yoy_growth: Optional[float]
