from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import AsyncGenerator

from db.models import User
from services.auth.jwt_service import JwtService
from presentation.dependencies import get_uow_dependency
from db.uow import SQLAlchemyUnitOfWork

security = HTTPBearer()
jwt_service = JwtService()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency)
) -> User:
    """
    FastAPI Dependency для проверки JWT Access токена и прав суперпользователя.
    Используется для защиты эндпоинтов админ-панели (например: /api/v1/admin/users).
    """
    token = credentials.credentials
    user_id = jwt_service.verify_token(token, "access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = await uow.user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    return user
