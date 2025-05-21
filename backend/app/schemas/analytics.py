# backend/app/schemas/analytics.py

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class PeriodEnum(str, Enum):
    MONTH = "month"
    QUARTER = "quarter"


class TimeSeriesItem(BaseModel):
    period: str  # например, "2025-05" или "2025-Q2"
    value: float


class ServiceMetric(BaseModel):
    service_name: str
    total_amount: float


class ClientAnalytics(BaseModel):
    client_id: int
    total_estimates: int
    total_estimates_period: Optional[int]  # если заданы start_date/end_date
    total_amount: float
    total_amount_period: Optional[float]
    average_amount: float
    # для графика динамики (месяц или квартал)
    timeseries: List[TimeSeriesItem]
    top_services: List[ServiceMetric]


class GlobalAnalytics(BaseModel):
    total_estimates: int
    total_amount: float
    average_amount: float
    timeseries: List[TimeSeriesItem]
    top_clients: List[ServiceMetric]       # переиспользуем ServiceMetric: здесь service_name = client_name
    by_responsible: List[ServiceMetric]    # service_name = username
    seasonality: List[TimeSeriesItem]      # сравнение периодов
    top_services: List[ServiceMetric]
