from fastapi import APIRouter

router = APIRouter(tags=["public"])


@router.get("/health", summary="Basic health check")
async def health_check() -> dict[str, str]:
    """
    Minimal health check endpoint to verify that the FastAPI server is running.
    """
    return {"status": "ok"}


def init_router(app) -> None:
    app.include_router(router)