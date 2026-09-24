import math
from datetime import datetime, timedelta
from statistics import median

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Dataset, ForecastRun, ForecastPoint, TimeSeriesPoint
from app.db.session import get_db
from app.schemas.forecasts import ForecastPointOut, ForecastRunOut, ForecastRunRequest

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("", response_model=list[ForecastRunOut])
def list_forecasts(db: Session = Depends(get_db)) -> list[ForecastRun]:
    return list(db.scalars(select(ForecastRun).order_by(ForecastRun.created_at.desc()).limit(100)).all())


@router.get("/{run_id}", response_model=ForecastRunOut)
def get_forecast_run(run_id: int, db: Session = Depends(get_db)) -> ForecastRun:
    run = db.get(ForecastRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="预测运行记录不存在")
    return run


@router.get("/{run_id}/points", response_model=list[ForecastPointOut])
def list_forecast_points(run_id: int, db: Session = Depends(get_db)) -> list[ForecastPoint]:
    if db.get(ForecastRun, run_id) is None:
        raise HTTPException(status_code=404, detail="预测运行记录不存在")
    return list(db.scalars(
        select(ForecastPoint)
        .where(ForecastPoint.run_id == run_id)
        .order_by(ForecastPoint.target_at.asc())
    ).all())


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    from calendar import monthrange

    return value.replace(year=year, month=month, day=min(value.day, monthrange(year, month)[1]))


def _target_time(last_at: datetime, horizon: str) -> datetime:
    if horizon == "5m":
        return last_at + timedelta(minutes=5)
    if horizon == "30m":
        return last_at + timedelta(minutes=30)
    if horizon == "1d":
        return last_at + timedelta(days=1)
    if horizon == "1m":
        return _add_months(last_at, 1)
    return _add_months(last_at, 3)


@router.post("/run", response_model=ForecastRunOut, status_code=201)
def create_forecast_run(request: ForecastRunRequest, db: Session = Depends(get_db)) -> ForecastRun:
    dataset = db.get(Dataset, request.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if request.model_name not in {"naive_baseline", "last_value"}:
        raise HTTPException(status_code=422, detail="当前只支持 naive_baseline（最后观测值延续）模型")

    observations = list(db.execute(
        select(TimeSeriesPoint.observed_at, TimeSeriesPoint.value)
        .where(TimeSeriesPoint.dataset_id == dataset.id)
        .order_by(TimeSeriesPoint.observed_at.asc())
    ).all())
    if len(observations) < 8:
        raise HTTPException(status_code=422, detail="至少需要 8 个时间点才能运行基线预测和滚动验证")

    intervals = [
        (observations[index][0] - observations[index - 1][0]).total_seconds()
        for index in range(1, len(observations))
        if observations[index][0] > observations[index - 1][0]
    ]
    if not intervals:
        raise HTTPException(status_code=422, detail="数据集缺少可用于推断频率的时间间隔")
    cadence_seconds = median(intervals)
    last_at = observations[-1][0]
    end_at = _target_time(last_at, request.horizon)
    if (end_at - last_at).total_seconds() < cadence_seconds:
        raise HTTPException(
            status_code=422,
            detail=f"数据中位采样间隔约 {cadence_seconds:g} 秒，无法支持短于采样间隔的预测周期",
        )
    horizon_steps = max(1, math.ceil((end_at - last_at).total_seconds() / cadence_seconds))
    if horizon_steps > 10000:
        raise HTTPException(status_code=422, detail="该预测周期相对数据频率过长，单次最多生成 10,000 个预测点")
    if len(observations) < horizon_steps + 6:
        raise HTTPException(
            status_code=422,
            detail=f"当前数据仅 {len(observations)} 个点，无法对该周期（约 {horizon_steps} 个采样间隔）进行有效滚动验证",
        )

    values = [float(row[1]) for row in observations]
    first_origin = max(5, len(values) - max(horizon_steps * 10, 40))
    origins = list(range(first_origin, len(values) - horizon_steps + 1))
    if len(origins) > 30:
        stride = math.ceil(len(origins) / 30)
        origins = origins[::stride][-30:]
    errors = [values[origin + horizon_steps - 1] - values[origin - 1] for origin in origins]
    abs_errors = sorted(abs(error) for error in errors)
    interval_index = max(0, math.ceil(len(abs_errors) * 0.9) - 1)
    error_band = abs_errors[interval_index] if abs_errors else 0.0
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    nonzero_actuals = [
        abs(errors[index]) / abs(values[origin + horizon_steps - 1])
        for index, origin in enumerate(origins)
        if values[origin + horizon_steps - 1] != 0
    ]
    run = ForecastRun(
        dataset_id=dataset.id,
        horizon=request.horizon,
        model_name="naive_baseline",
        model_version="1.0.0",
        validation_method=request.validation_method,
        status="validated" if len(errors) >= 10 else "weak_signal",
        training_window={
            "first_at": observations[0][0].isoformat(),
            "last_at": last_at.isoformat(),
            "sample_count": len(observations),
            "median_cadence_seconds": cadence_seconds,
            "forecast_steps": horizon_steps,
        },
        validation_metrics={
            "method": request.validation_method,
            "backtest_origin_count": len(errors),
            "mae": mae,
            "rmse": rmse,
            "mape": sum(nonzero_actuals) / len(nonzero_actuals) if nonzero_actuals else None,
            "empirical_absolute_error_p90": error_band,
            "baseline": "last_observation_value",
        },
    )
    db.add(run)
    db.flush()
    forecast_points = []
    for step in range(1, horizon_steps + 1):
        target_at = end_at if step == horizon_steps else last_at + timedelta(seconds=cadence_seconds * step)
        forecast_points.append(ForecastPoint(
            run_id=run.id,
            target_at=target_at,
            predicted_value=values[-1],
            lower_bound=values[-1] - error_band,
            upper_bound=values[-1] + error_band,
        ))
    db.add_all(forecast_points)
    db.commit()
    db.refresh(run)
    return run
