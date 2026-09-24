from fastapi import APIRouter

from app.schemas.common import DataStatus, EmptyCollection, HealthResponse

api_router = APIRouter()


@api_router.get("/health", tags=["system"], response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="api", data_status="not_connected")


@api_router.get("/overview", tags=["overview"])
def overview() -> dict[str, object]:
    """Explicit empty state until verified market data is connected."""
    return {
        "instrument": {"symbol": "BU", "name": "石油沥青期货"},
        "data_status": DataStatus.unavailable,
        "as_of": None,
        "message": "尚未接入并验证行情数据源",
        "market": None,
        "contracts": [],
        "forecasts": [],
    }


@api_router.get("/market", tags=["market"], response_model=EmptyCollection)
def market_data() -> EmptyCollection:
    return EmptyCollection(data_status="unavailable", as_of=None, message="尚无已验证的行情数据")


@api_router.get("/fundamentals", tags=["fundamentals"], response_model=EmptyCollection)
def fundamentals() -> EmptyCollection:
    return EmptyCollection(data_status="unavailable", as_of=None, message="尚无已验证的基本面数据")


@api_router.get("/forecasts", tags=["forecasts"], response_model=EmptyCollection)
def forecasts() -> EmptyCollection:
    return EmptyCollection(data_status="unavailable", as_of=None, message="尚无可验证的模型预测结果")


@api_router.get("/contracts", tags=["contracts"], response_model=EmptyCollection)
def contracts() -> EmptyCollection:
    return EmptyCollection(data_status="unavailable", as_of=None, message="尚未配置主力合约识别与合约数据")


@api_router.get("/news", tags=["news"], response_model=EmptyCollection)
def news() -> EmptyCollection:
    return EmptyCollection(data_status="unavailable", as_of=None, message="尚未接入并验证资讯来源")


@api_router.get("/models", tags=["models"], response_model=EmptyCollection)
def models() -> EmptyCollection:
    return EmptyCollection(data_status="unavailable", as_of=None, message="尚无已注册的模型与训练结果")
