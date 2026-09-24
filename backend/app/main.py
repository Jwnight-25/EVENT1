from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title="沥青期货智能分析平台 API",
    version="0.1.0",
    description="BU 期货研究平台的初始 API 骨架。当前未连接真实数据源。",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "bitumen-analysis-api", "docs": "/docs"}
