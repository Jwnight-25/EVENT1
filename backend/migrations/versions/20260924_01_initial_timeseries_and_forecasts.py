"""Create dataset, time-series, forecast, and explanation tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260924_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("instrument", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("frequency", sa.String(length=40), nullable=False),
        sa.Column("timezone_name", sa.String(length=80), nullable=False),
        sa.Column("time_column", sa.String(length=120), nullable=False),
        sa.Column("value_column", sa.String(length=120), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_datasets_name", "datasets", ["name"])
    op.create_index("ix_datasets_instrument", "datasets", ["instrument"])
    op.create_index("ix_datasets_frequency", "datasets", ["frequency"])

    op.create_table(
        "time_series_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("raw_value", sa.String(length=200), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.UniqueConstraint("dataset_id", "observed_at", name="uq_series_time"),
    )
    op.create_index("ix_time_series_points_dataset_id", "time_series_points", ["dataset_id"])
    op.create_index("ix_time_series_points_observed_at", "time_series_points", ["observed_at"])
    op.create_index("ix_series_time", "time_series_points", ["dataset_id", "observed_at"])

    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("horizon", sa.String(length=20), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("validation_method", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("training_window", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_forecast_runs_dataset_id", "forecast_runs", ["dataset_id"])
    op.create_index("ix_forecast_runs_horizon", "forecast_runs", ["horizon"])
    op.create_index("ix_forecast_runs_status", "forecast_runs", ["status"])

    op.create_table(
        "forecast_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("lower_bound", sa.Float(), nullable=True),
        sa.Column("upper_bound", sa.Float(), nullable=True),
        sa.Column("actual_value", sa.Float(), nullable=True),
    )
    op.create_index("ix_forecast_points_run_id", "forecast_points", ["run_id"])
    op.create_index("ix_forecast_points_target_at", "forecast_points", ["target_at"])
    op.create_index("ix_forecast_run_target", "forecast_points", ["run_id", "target_at"])

    op.create_table(
        "ai_explanations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("forecast_run_id", sa.Integer(), sa.ForeignKey("forecast_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_model", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("web_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_explanations")
    op.drop_index("ix_forecast_run_target", table_name="forecast_points")
    op.drop_index("ix_forecast_points_target_at", table_name="forecast_points")
    op.drop_index("ix_forecast_points_run_id", table_name="forecast_points")
    op.drop_table("forecast_points")
    op.drop_index("ix_forecast_runs_status", table_name="forecast_runs")
    op.drop_index("ix_forecast_runs_horizon", table_name="forecast_runs")
    op.drop_index("ix_forecast_runs_dataset_id", table_name="forecast_runs")
    op.drop_table("forecast_runs")
    op.drop_index("ix_series_time", table_name="time_series_points")
    op.drop_index("ix_time_series_points_observed_at", table_name="time_series_points")
    op.drop_index("ix_time_series_points_dataset_id", table_name="time_series_points")
    op.drop_table("time_series_points")
    op.drop_index("ix_datasets_frequency", table_name="datasets")
    op.drop_index("ix_datasets_instrument", table_name="datasets")
    op.drop_index("ix_datasets_name", table_name="datasets")
    op.drop_table("datasets")
