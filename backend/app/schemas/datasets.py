from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    instrument: str
    description: str | None
    source_name: str
    source_url: str | None
    unit: str
    frequency: str
    timezone_name: str
    time_column: str
    value_column: str
    imported_at: datetime


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    observed_at: datetime
    value: float
    raw_value: str
    source_row: int


class DatasetImportResult(BaseModel):
    dataset: DatasetOut
    rows_read: int
    rows_imported: int
    rows_duplicate: int
