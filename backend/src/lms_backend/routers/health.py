import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from lms_backend.database import engine
from lms_backend.services.llm.qwen_client import QwenClient
from lms_backend.settings import settings

router = APIRouter()


@router.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}


@router.get('/health/db')
async def health_db() -> dict[str, str]:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": str(exc)},
        )
    return {"status": "ok"}


@router.get('/health/llm')
async def health_llm():
    try:
        return await QwenClient().healthcheck()
    except httpx.HTTPError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "detail": str(exc),
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "detail": str(exc),
            },
        )
