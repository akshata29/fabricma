import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.middleware.correlation import CorrelationIDMiddleware
from app.middleware.logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    # Suppress verbose SDK logging that adds noise without value
    for noisy in ("azure.core", "azure.identity", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FabricMA API",
        version="1.0.0",
        lifespan=lifespan,
    )
    cors_origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.include_router(api_router)
    return app


app = create_app()
