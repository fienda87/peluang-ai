from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
