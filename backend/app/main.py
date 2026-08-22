from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth_routes import router as auth_router
from app.api.behavior_routes import router as behavior_router
from app.api.opportunity_routes import router as opportunity_router
from app.api.recommendation_routes import router as recommendation_router
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

app.include_router(auth_router)
app.include_router(opportunity_router)
app.include_router(recommendation_router)
app.include_router(behavior_router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
