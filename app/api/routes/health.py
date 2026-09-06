from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    summary="Verificar el estado de la API",
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "BCP Tablero NPS API is running",
    }