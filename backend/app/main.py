from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin_pipeline import router as admin_pipeline_router
from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.api.behavior_routes import router as behavior_router
from app.api.middleware import RateLimitMiddleware
from app.api.opportunity_routes import router as opportunity_router
from app.api.profile_routes import router as profile_router
from app.api.recommendation_routes import router as recommendation_router
from app.api.stream_routes import router as pipeline_stream_router
from app.api.telegram_routes import router as telegram_router
from app.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_started")
    yield
    logger.info("app_stopped")


app = FastAPI(
    title="Peluang.ai",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router)
app.include_router(opportunity_router)
app.include_router(recommendation_router)
app.include_router(behavior_router)
app.include_router(profile_router)
app.include_router(admin_router)
app.include_router(admin_pipeline_router)
app.include_router(pipeline_stream_router)
app.include_router(telegram_router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
