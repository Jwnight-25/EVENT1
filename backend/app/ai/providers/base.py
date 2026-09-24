from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class WebSource:
    title: str
    url: str


@dataclass(frozen=True)
class ExplanationResult:
    provider: str
    model: str
    text: str
    sources: list[WebSource] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None


class ExplanationProvider(Protocol):
    name: str

    def explain(self, *, question: str, evidence: dict[str, object], web_search: bool) -> ExplanationResult:
        """Explain supplied, validated results without generating new predictions."""
