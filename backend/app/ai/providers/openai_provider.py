import json

from openai import OpenAI, OpenAIError

from app.ai.providers.base import ExplanationResult, WebSource
from app.core.config import settings


class ProviderNotConfigured(RuntimeError):
    pass


class ProviderRequestFailed(RuntimeError):
    pass


class OpenAIExplanationProvider:
    name = "openai"
    prompt_version = "forecast-explanation-v1"

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ProviderNotConfigured("OPENAI_API_KEY 未配置")
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=45.0, max_retries=1)

    def explain(self, *, question: str, evidence: dict[str, object], web_search: bool) -> ExplanationResult:
        instructions = (
            "你是期货研究结果解释助手。只解释输入中已验证的量化模型结果和数据。"
            "不得计算、修改或编造价格、方向、概率、置信区间或模型指标；缺少证据时明确说数据不足。"
            "清楚区分输入证据与联网查到的背景资料。联网资料必须给出来源，不得把新闻相关性说成因果关系。"
            "使用简体中文，简洁、专业，不提供交易指令。"
        )
        prompt = f"用户问题：{question}\n已验证的模型与数据上下文：\n{json.dumps(evidence, ensure_ascii=False, default=str)}"
        tools = []
        if web_search and settings.ai_web_search_enabled:
            tools.append({"type": "web_search", "search_context_size": "low", "external_web_access": True})
        try:
            response = self.client.responses.create(
                model=settings.openai_model,
                reasoning={"effort": "low"},
                instructions=instructions,
                input=prompt,
                tools=tools,
            )
        except OpenAIError as exc:
            raise ProviderRequestFailed("OpenAI API 请求失败，请检查密钥、额度和网络连接") from exc

        sources: list[WebSource] = []
        for item in response.output:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []):
                for annotation in getattr(content, "annotations", []) or []:
                    if getattr(annotation, "type", None) == "url_citation":
                        url = getattr(annotation, "url", None)
                        if url and all(source.url != url for source in sources):
                            sources.append(WebSource(title=getattr(annotation, "title", "网页来源"), url=url))

        usage = response.usage
        return ExplanationResult(
            provider=self.name,
            model=settings.openai_model,
            text=response.output_text,
            sources=sources,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )
