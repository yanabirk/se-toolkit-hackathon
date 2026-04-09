import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from lms_backend.auth import verify_api_key
from lms_backend.database import init_db
from lms_backend.routers import (
    generation,
    health,
    materials,
    study_plans,
    study_sessions,
    telegram_users,
    users,
)
from lms_backend.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").propagate = True
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="Study planner backend API.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.exception(
        "unhandled_exception",
        extra={"event": "unhandled_exception", "path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content=(
            {
                "detail": str(exc),
                "type": type(exc).__name__,
                "path": request.url.path,
                "traceback": tb[-3:],
            }
            if settings.debug
            else {
                "detail": "Internal server error",
                "type": type(exc).__name__,
                "path": request.url.path,
            }
        ),
    )


@app.middleware("http")
async def log_requests(request: Request, call_next: RequestResponseEndpoint) -> Response:
    t0 = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - t0) * 1000)
    logger.info(
        "request_completed",
        extra={
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])

secured_dependencies = [Depends(verify_api_key)]
app.include_router(
    telegram_users.router,
    prefix="/api/v1/telegram-users",
    tags=["telegram-users"],
    dependencies=secured_dependencies,
)
app.include_router(
    study_plans.router,
    prefix="/api/v1/study-plans",
    tags=["study-plans"],
    dependencies=secured_dependencies,
)
app.include_router(
    study_sessions.router,
    prefix="/api/v1/study-sessions",
    tags=["study-sessions"],
    dependencies=secured_dependencies,
)
app.include_router(
    materials.router,
    prefix="/api/v1/materials",
    tags=["materials"],
    dependencies=secured_dependencies,
)
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=secured_dependencies,
)
app.include_router(
    generation.router,
    prefix="/api/v1/study-plans",
    tags=["generation"],
    dependencies=secured_dependencies,
)
app.include_router(
    generation.router,
    prefix="/api/v1/generation/study-plans",
    tags=["generation-legacy"],
    dependencies=secured_dependencies,
)
