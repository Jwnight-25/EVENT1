from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers.openai_provider import (
    OpenAIExplanationProvider,
    ProviderNotConfigured,
    ProviderRequestFailed,
)
from app.core.config import settings
from app.db.models import AIExplanation, Dataset, ForecastPoint, ForecastRun
from app.db.session import get_db
from app.schemas.ai import AIExplanationOut, AIExplanationRequest, WebSourceOut

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/capabilities")
def ai_capabilities() -> dict[str, object]:
    return {
        "default_provider": settings.ai_provider,
        "default_model": settings.openai_model if settings.ai_provider == "openai" else None,
        "web_search_enabled": settings.ai_web_search_enabled,
        "api_key_configured": bool(settings.openai_api_key),
        "purpose": "解释已验证的模型结果；不负责生成量化预测",
        "providers": ["openai", "google", "anthropic"],
    }


@router.get("/explanations/{explanation_id}", response_model=AIExplanationOut)
def get_explanation(explanation_id: int, db: Session = Depends(get_db)) -> AIExplanationOut:
    row = db.get(AIExplanation, explanation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="解释记录不存在")
    return AIExplanationOut(
        id=row.id,
        provider=row.provider,
        model=row.provider_model,
        explanation=row.explanation,
        sources=[WebSourceOut(**source) for source in row.web_sources],
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        created_at=row.created_at or datetime.now(timezone.utc),
    )


@router.post("/explanations", response_model=AIExplanationOut, status_code=201)
def explain_results(request: AIExplanationRequest, db: Session = Depends(get_db)) -> AIExplanationOut:
    if settings.ai_provider != "openai":
        raise HTTPException(status_code=501, detail=f"当前尚未实现 {settings.ai_provider} provider")
    run = db.get(ForecastRun, request.forecast_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="预测运行记录不存在")
    if run.status != "validated":
        raise HTTPException(status_code=422, detail="仅可解释已验证的预测运行结果")
    dataset = db.get(Dataset, run.dataset_id)
    points = list(db.scalars(
        select(ForecastPoint)
        .where(ForecastPoint.run_id == run.id)
        .order_by(ForecastPoint.target_at.desc())
        .limit(20)
    ).all())
    evidence = {
        "forecast_run_id": run.id,
        "status": run.status,
        "instrument": dataset.instrument if dataset else None,
        "dataset": dataset.name if dataset else None,
        "source_name": dataset.source_name if dataset else None,
        "unit": dataset.unit if dataset else None,
        "frequency": dataset.frequency if dataset else None,
        "horizon": run.horizon,
        "model_name": run.model_name,
        "model_version": run.model_version,
        "validation_method": run.validation_method,
        "training_window": run.training_window,
        "validation_metrics": run.validation_metrics,
        "forecast_points": [
            {
                "target_at": point.target_at.isoformat(),
                "predicted_value": point.predicted_value,
                "lower_bound": point.lower_bound,
                "upper_bound": point.upper_bound,
                "actual_value": point.actual_value,
            }
            for point in reversed(points)
        ],
    }
    try:
        provider = OpenAIExplanationProvider()
        result = provider.explain(
            question=request.question,
            evidence=evidence,
            web_search=request.web_search,
        )
    except ProviderNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderRequestFailed as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    row = AIExplanation(
        forecast_run_id=run.id,
        provider=result.provider,
        provider_model=result.model,
        prompt_version=OpenAIExplanationProvider.prompt_version,
        explanation=result.text,
        evidence_context=evidence,
        web_sources=[{"title": source.title, "url": source.url} for source in result.sources],
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AIExplanationOut(
        id=row.id,
        provider=row.provider,
        model=row.provider_model,
        explanation=row.explanation,
        sources=[WebSourceOut(**source) for source in row.web_sources],
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        created_at=row.created_at or datetime.now(timezone.utc),
    )
