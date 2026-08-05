from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging

from app.api.routes import router
from app.core.config import get_settings
from app.api.middleware import (
    RequestLogMiddleware
)


settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 合同分析服务",
)

app.add_middleware(
    CORSMiddleware,
    RequestLogMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.app_version,
    }
