from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from config.settings import get_settings
from presentation.dependencies.security import get_current_admin
from db.models import User
from services.auth.cache_auth_repo import CacheAuthRepository
from services.auth.jwt_service import JwtService
from services.providers.cache.mock_cache import MockCacheProvider

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])

# Инициализируем провайдер кэша один раз на модуль (in-memory)
_cache_provider = MockCacheProvider()
_auth_repo = CacheAuthRepository(_cache_provider)
_jwt_service = JwtService()


class InitAuthResponse(BaseModel):
    token: str
    deep_link: str


class AuthStatusResponse(BaseModel):
    status: str
    access_token: str | None = None
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileResponse(BaseModel):
    name: str
    role: str
    avatar: str | None = None
    username: str | None = None
    bot_username: str | None = None


@router.get("/me", response_model=ProfileResponse)
async def get_current_profile(admin: User = Depends(get_current_admin)):
    """Возвращает данные текущего авторизованного админа."""
    settings = get_settings()
    name = admin.full_name or (f"{admin.first_name or ''} {admin.last_name or ''}".strip()) or f"User #{admin.user_id}"
    bot_username = settings.BOT_USERNAME.replace("@", "") if settings.BOT_USERNAME else None
    return ProfileResponse(
        name=name,
        role="Суперадмин" if admin.is_superuser else "Админ",
        avatar=None,
        username=admin.username,
        bot_username=bot_username,
    )


@router.post("/init", response_model=InitAuthResponse)
async def init_auth():
    """
    Создает временную сессию (UUID) и возвращает deep link для перехода в Telegram бота.
    """
    settings = get_settings()
    token = await _auth_repo.create_auth_session()
    
    # Ссылка вида https://t.me/BotUsername?start=auth_12345
    # Заменяем @ на всякий случай, если имя бота передано как @username
    bot_username = settings.BOT_USERNAME.replace("@", "") 
    deep_link = f"https://t.me/{bot_username}?start=auth_{token}"
    
    return InitAuthResponse(token=token, deep_link=deep_link)


@router.get("/status", response_model=AuthStatusResponse)
async def check_auth_status(token: str):
    """
    Проверяет статус авторизации (для polling'а Next.js).
    """
    session = await _auth_repo.get_session(token)
    if not session:
        return AuthStatusResponse(status="expired")
        
    status = session.get("status")
    
    if status == "approved":
        user_id = session.get("user_id")
        if not user_id:
            return AuthStatusResponse(status="error")
            
        # Удаляем временный токен из кэша
        await _auth_repo.delete_session(token)
        
        # Генерируем постоянные JWT
        access_token = _jwt_service.create_access_token(user_id)
        refresh_token = _jwt_service.create_refresh_token(user_id)
        
        return AuthStatusResponse(
            status="approved", 
            access_token=access_token, 
            refresh_token=refresh_token
        )
        
    return AuthStatusResponse(status=status) # pending, rejected


@router.post("/refresh", response_model=AuthStatusResponse)
async def refresh_tokens(request: RefreshRequest):
    """
    Обновляет Access и Refresh токены по действующему Refresh Token'у.
    """
    user_id = _jwt_service.verify_token(request.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    access_token = _jwt_service.create_access_token(user_id)
    refresh_token = _jwt_service.create_refresh_token(user_id)
    
    return AuthStatusResponse(
        status="approved", 
        access_token=access_token, 
        refresh_token=refresh_token
    )
