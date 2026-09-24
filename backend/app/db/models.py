from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    instrument: Mapped[str] = mapped_column(String(30), default="BU", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(80))
    frequency: Mapped[str] = mapped_column(String(40), index=True)
    timezone_name: Mapped[str] = mapped_column(String(80), default="Asia/Shanghai")
    time_column: Mapped[str] = mapped_column(String(120))
    value_column: Mapped[str] = mapped_column(String(120))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    points: Mapped[list["TimeSeriesPoint"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class TimeSeriesPoint(Base):
    __tablename__ = "time_series_points"
    __table_args__ = (
        UniqueConstraint("dataset_id", "observed_at", name="uq_series_time"),
        Index("ix_series_time", "dataset_id", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[float] = mapped_column(Float)
    raw_value: Mapped[str] = mapped_column(String(200))
    source_row: Mapped[int] = mapped_column(Integer)
    dataset: Mapped[Dataset] = relationship(back_populates="points")


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="RESTRICT"), index=True)
    horizon: Mapped[str] = mapped_column(String(20), index=True)
    model_name: Mapped[str] = mapped_column(String(120))
    model_version: Mapped[str] = mapped_column(String(80))
    validation_method: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="created", index=True)
    training_window: Mapped[dict] = mapped_column(JSONB, default=dict)
    validation_metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    points: Mapped[list["ForecastPoint"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class ForecastPoint(Base):
    __tablename__ = "forecast_points"
    __table_args__ = (Index("ix_forecast_run_target", "run_id", "target_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True)
    target_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    predicted_value: Mapped[float] = mapped_column(Float)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    run: Mapped[ForecastRun] = relationship(back_populates="points")


class AIExplanation(Base):
    __tablename__ = "ai_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    forecast_run_id: Mapped[int | None] = mapped_column(ForeignKey("forecast_runs.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text)
    evidence_context: Mapped[dict] = mapped_column(JSONB, default=dict)
    web_sources: Mapped[list] = mapped_column(JSONB, default=list)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
