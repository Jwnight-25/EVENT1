from fastapi import APIRouter

from app.api.routes import ai, datasets, forecasts
from app.schemas.common import DataStatus, EmptyCollection, HealthResponse

api_router = APIRouter()
api_router.include_router(datasets.router)
api_router.include_router(forecasts.router)
api_router.include_router(ai.router)


@api_router.get("/health", tags=["system"], response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="api", data_status="not_checked")


@api_router.get("/overview", tags=["overview"])
def overview() -> dict[str, object]:
    return {
        "instrument": {"symbol": "BU", "name": "石油沥青期货"},
        "data_status": DataStatus.unavailable,
        "as_of": None,
        "message": "尚未接入并验证行情数据源",
        "market": None,
        "contracts": [],
        "forecasts": [],
    }


def _unavailable(message: str) -> EmptyCollection:
    return EmptyCollection(data_status=DataStatus.unavailable, as_of=None, message=message)


@api_router.get("/market", tags=["market"], response_model=EmptyCollection)
def market_data() -> EmptyCollection:
    return _unavailable("行情视图接口已预留；当前尚无来源数据")


@api_router.get("/fundamentals", tags=["fundamentals"], response_model=EmptyCollection)
def fundamentals() -> EmptyCollection:
    return _unavailable("基本面接口已预留；请先导入并分类时间序列数据")


@api_router.get("/contracts", tags=["contracts"], response_model=EmptyCollection)
def contracts() -> EmptyCollection:
    return _unavailable("合约接口已预留；尚未配置合约主数据")


@api_router.get("/news", tags=["news"], response_model=EmptyCollection)
def news() -> EmptyCollection:
    return _unavailable("资讯接口已预留；当前尚无已验证资讯来源")


@api_router.get("/models", tags=["models"], response_model=EmptyCollection)
def models() -> EmptyCollection:
    return _unavailable("模型注册接口已预留；尚未训练或注册模型")
