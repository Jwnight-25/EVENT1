from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Observation(BaseModel):
    """A source-traceable value; keep the original value alongside normalized data."""

    model_config = ConfigDict(extra="forbid")

    instrument: str = Field(examples=["BU"])
    contract: str | None = None
    field: str
    value: float | None = None
    raw_value: str | None = None
    unit: str | None = None
    frequency: str
    source: str
    observed_at: datetime
    published_at: datetime | None = None
    fetched_at: datetime
    quality_status: str = "unverified"
