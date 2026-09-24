from enum import StrEnum

from pydantic import BaseModel, Field


class DataStatus(StrEnum):
    available = "available"
    partial = "partial"
    unavailable = "unavailable"


class HealthResponse(BaseModel):
    status: str
    service: str
    data_status: str


class EmptyCollection(BaseModel):
    data_status: DataStatus
    as_of: str | None
    message: str
    items: list[dict[str, object]] = Field(default_factory=list)
