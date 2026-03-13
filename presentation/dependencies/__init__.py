"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from typing import AsyncGenerator

from db.uow import SQLAlchemyUnitOfWork


async def get_uow_dependency() -> AsyncGenerator[SQLAlchemyUnitOfWork, None]:
    """
    Dependency to get SQLAlchemyUnitOfWork instance for FastAPI endpoints.
    
    Usage:
        @app.get("/users")
        async def get_users(uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency)):
            user = await uow.user_repo.get(1)
            ...
    """
    async with SQLAlchemyUnitOfWork() as uow:
        yield uow
        # Transaction is committed or rolled back automatically on exit.


__all__ = [
    "get_uow_dependency",
]
