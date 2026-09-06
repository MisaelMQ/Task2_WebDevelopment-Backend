from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.responses import router as responses_router
from app.api.routes.sources import router as sources_router
from app.api.routes.channels import router as channels_router
from app.api.routes.surveys import router as surveys_router
from app.core.config import get_settings
from app.db.application import initialize_application_database

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_application_database()
    yield

app = FastAPI(
    title=settings.app_name,
    description=(
        "REST API para la consulta y administración "
        "de información NPS."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    sources_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    responses_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    channels_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    surveys_router,
    prefix=settings.api_v1_prefix,
)

@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "message": settings.app_name,
        "documentation": "/docs",
    }