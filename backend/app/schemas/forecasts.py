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
