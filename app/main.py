from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(
    title="BCP Tablero NPS API",
    description="REST API para la consulta y administración de información Encuestas NPS.",
    version="0.1.0",
)

app.include_router(
    health_router,
    prefix="/api/v1",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "message": "BCP Tablero NPS API",
        "documentation": "/docs",
    }