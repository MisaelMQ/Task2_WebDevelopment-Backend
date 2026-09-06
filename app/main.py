from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.responses import router as responses_router
from app.api.routes.sources import router as sources_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="REST API para la consulta y administración de información Encuestas NPS.",
    version=settings.app_version,
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

@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "message": settings.app_name,
        "documentation": "/docs",
    }