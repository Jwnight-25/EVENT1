from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Forecast(BaseModel):
    """Forecast contract. Probabilities and intervals must come from validated models."""

    model_config = ConfigDict(extra="forbid")

    instrument: str = "BU"
    contract: str | None = None
    horizon: Literal["5m", "30m", "1d", "1m", "3m"]
    direction: Literal["up", "down", "sideways"] | None = None
    probability_up: float | None = Field(default=None, ge=0, le=1)
    predicted_price: float | None = None
    interval_lower: float | None = None
    interval_upper: float | None = None
    confidence_label: Literal["low", "medium", "high"] | None = None
    model_name: str
    model_version: str
    generated_at: datetime
    validation_status: Literal["validated", "weak_signal", "insufficient_data"]
    drivers: list[str] = Field(default_factory=list)


class ForecastRunRequest(BaseModel):
    dataset_id: int = Field(gt=0)
    horizon: Literal["5m", "30m", "1d", "1m", "3m"]
    model_name: str = "naive_baseline"
    validation_method: Literal["walk_forward", "expanding_window", "rolling_window"] = "walk_forward"


class ForecastPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_at: datetime
    predicted_value: float
    lower_bound: float | None
    upper_bound: float | None
    actual_value: float | None


class ForecastRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    horizon: str
    model_name: str
    model_version: str
    validation_method: str
    status: str
    validation_metrics: dict[str, object]
    created_at: datetime
