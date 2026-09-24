from datetime import datetime

from pydantic import BaseModel, Field


class AIExplanationRequest(BaseModel):
    question: str = Field(min_length=1, max_length=3000)
    forecast_run_id: int = Field(gt=0)
    web_search: bool = True


class WebSourceOut(BaseModel):
    title: str
    url: str


class AIExplanationOut(BaseModel):
    id: int
    provider: str
    model: str
    explanation: str
    sources: list[WebSourceOut]
    input_tokens: int | None
    output_tokens: int | None
    created_at: datetime
