import csv
import io
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Dataset, TimeSeriesPoint
from app.db.session import get_db
from app.schemas.datasets import DatasetImportResult, DatasetOut, ObservationOut

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _parse_timestamp(raw: str, timezone_name: str) -> datetime:
    value = raw.strip()
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        for pattern in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(value, pattern)
                break
            except ValueError:
                continue
    if parsed is None:
        raise ValueError(f"无法识别时间格式：{value}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed.astimezone(timezone.utc)


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    instrument: str | None = Query(default=None, min_length=2, max_length=30),
    db: Session = Depends(get_db),
) -> list[Dataset]:
    statement = select(Dataset)
    if instrument:
        statement = statement.where(Dataset.instrument == instrument.upper())
    return list(db.scalars(statement.order_by(Dataset.imported_at.desc())).all())


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return dataset


@router.get("/{dataset_id}/observations", response_model=list[ObservationOut])
def list_observations(
    dataset_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5000, ge=1, le=50000),
    db: Session = Depends(get_db),
) -> list[TimeSeriesPoint]:
    if db.get(Dataset, dataset_id) is None:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start 必须早于或等于 end")
    statement = select(TimeSeriesPoint).where(TimeSeriesPoint.dataset_id == dataset_id)
    if start:
        statement = statement.where(TimeSeriesPoint.observed_at >= start)
    if end:
        statement = statement.where(TimeSeriesPoint.observed_at <= end)
    statement = statement.order_by(TimeSeriesPoint.observed_at.asc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{dataset_id}/chart")
def chart_series(
    dataset_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=10000, ge=1, le=50000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="数据集不存在")
    statement = select(TimeSeriesPoint.observed_at, TimeSeriesPoint.value).where(
        TimeSeriesPoint.dataset_id == dataset_id
    )
    if start:
        statement = statement.where(TimeSeriesPoint.observed_at >= start)
    if end:
        statement = statement.where(TimeSeriesPoint.observed_at <= end)
    statement = statement.order_by(TimeSeriesPoint.observed_at.asc()).limit(limit)
    points = db.execute(statement).all()
    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "unit": dataset.unit,
        "frequency": dataset.frequency,
        "chart_type": "line",
        "x_field": "observed_at",
        "y_field": "value",
        "as_of": dataset.imported_at,
        "points": [{"observed_at": point[0], "value": point[1]} for point in points],
    }


@router.post("/import", response_model=DatasetImportResult, status_code=201)
async def import_csv(
    file: UploadFile = File(...),
    name: str = Form(..., min_length=1, max_length=200),
    unit: str = Form(..., min_length=1, max_length=80),
    frequency: str = Form(..., min_length=1, max_length=40),
    source_name: str = Form(..., min_length=1, max_length=200),
    time_column: str = Form(..., min_length=1, max_length=120),
    value_column: str = Form(..., min_length=1, max_length=120),
    instrument: str = Form(default="BU", max_length=30),
    timezone_name: str = Form(default="Asia/Shanghai", max_length=80),
    source_url: str | None = Form(default=None, max_length=2000),
    db: Session = Depends(get_db),
) -> DatasetImportResult:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="目前只支持 CSV 文件")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="timezone_name 不是有效时区") from exc

    payload = await file.read(settings.max_csv_upload_bytes + 1)
    if len(payload) > settings.max_csv_upload_bytes:
        raise HTTPException(status_code=413, detail="CSV 文件超过 25 MB 限制")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = payload.decode("gb18030")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail="文件编码需为 UTF-8 或 GB18030") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or time_column not in reader.fieldnames or value_column not in reader.fieldnames:
        raise HTTPException(status_code=422, detail="找不到指定的时间列或数值列")
    records: list[dict[str, object]] = []
    rows_read = 0
    for row_number, row in enumerate(reader, start=2):
        if not (row.get(time_column) or "").strip() and not (row.get(value_column) or "").strip():
            continue
        rows_read += 1
        try:
            observed_at = _parse_timestamp(row.get(time_column) or "", timezone_name)
            raw_value = (row.get(value_column) or "").strip()
            numeric_value = float(raw_value.replace(",", ""))
            if not math.isfinite(numeric_value):
                raise ValueError("数值不是有限数")
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=f"第 {row_number} 行无效：{exc}") from exc
        records.append({
            "observed_at": observed_at,
            "value": numeric_value,
            "raw_value": raw_value,
            "source_row": row_number,
        })
    if not records:
        raise HTTPException(status_code=422, detail="文件中没有可导入的数据行")

    dataset = Dataset(
        name=name,
        instrument=instrument,
        source_name=source_name,
        source_url=source_url,
        unit=unit,
        frequency=frequency,
        timezone_name=timezone_name,
        time_column=time_column,
        value_column=value_column,
    )
    db.add(dataset)
    db.flush()
    inserted = 0
    for offset in range(0, len(records), 1000):
        batch = [{"dataset_id": dataset.id, **record} for record in records[offset:offset + 1000]]
        result = db.execute(
            insert(TimeSeriesPoint)
            .values(batch)
            .on_conflict_do_nothing(constraint="uq_series_time")
            .returning(TimeSeriesPoint.id)
        )
        inserted += len(result.scalars().all())
    db.commit()
    db.refresh(dataset)
    return DatasetImportResult(
        dataset=dataset,
        rows_read=rows_read,
        rows_imported=inserted,
        rows_duplicate=len(records) - inserted,
    )


@router.get("/{dataset_id}/summary")
def dataset_summary(dataset_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="数据集不存在")
    summary = db.execute(
        select(
            func.count(TimeSeriesPoint.id),
            func.min(TimeSeriesPoint.observed_at),
            func.max(TimeSeriesPoint.observed_at),
            func.min(TimeSeriesPoint.value),
            func.max(TimeSeriesPoint.value),
        ).where(TimeSeriesPoint.dataset_id == dataset_id)
    ).one()
    return {
        "dataset_id": dataset_id,
        "data_status": "available" if summary[0] else "empty",
        "count": summary[0],
        "first_at": summary[1],
        "last_at": summary[2],
        "min_value": summary[3],
        "max_value": summary[4],
        "unit": dataset.unit,
        "frequency": dataset.frequency,
    }
