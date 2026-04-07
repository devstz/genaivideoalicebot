from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from config.settings import get_settings
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from db.uow import SQLAlchemyUnitOfWork
from db.models import User
from services.auth.cache_auth_repo import CacheAuthRepository
from services.auth.jwt_service import JwtService
from services.auth.password_service import PasswordService
from services.providers.cache.mock_cache import MockCacheProvider
from services.telegram_bot_username import ensure_resolved_bot_username

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])

# Инициализируем провайдер кэша один раз на модуль (in-memory)
_cache_provider = MockCacheProvider()
_auth_repo = CacheAuthRepository(_cache_provider)
_jwt_service = JwtService()
_password_service = PasswordService()


class InitAuthResponse(BaseModel):
    token: str
    deep_link: str


class AuthStatusResponse(BaseModel):
    status: str
    access_token: str | None = None
    refresh_token: str | None = None
    token: str | None = None
    deep_link: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordLoginRequest(BaseModel):
    login: str
    password: str


class BindAdminCredentialsRequest(BaseModel):
    login: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ToggleTwoFaRequest(BaseModel):
    enabled: bool


class ProfileResponse(BaseModel):
    user_id: int
    name: str
    role: str
    avatar: str | None = None
    username: str | None = None
    bot_username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    admin_login: str | None = None
    has_admin_credentials: bool
    admin_require_telegram_2fa: bool


class BindAdminCredentialsResponse(BaseModel):
    status: str


@router.get("/me", response_model=ProfileResponse)
async def get_current_profile(admin: User = Depends(get_current_admin)):
    """Возвращает данные текущего авторизованного админа."""
    settings = get_settings()
    name = admin.full_name or (f"{admin.first_name or ''} {admin.last_name or ''}".strip()) or f"User #{admin.user_id}"
    bot_username = await ensure_resolved_bot_username(settings)
    return ProfileResponse(
        user_id=admin.user_id,
        name=name,
        role="Суперадмин" if admin.is_superuser else "Админ",
        avatar=None,
        username=admin.username,
        first_name=admin.first_name,
        last_name=admin.last_name,
        bot_username=bot_username,
        admin_login=admin.admin_login,
        has_admin_credentials=bool(admin.admin_login and admin.admin_password_hash),
        admin_require_telegram_2fa=admin.admin_require_telegram_2fa,
    )


@router.post("/login", response_model=AuthStatusResponse)
async def login_with_password(
    request: PasswordLoginRequest,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
):
    settings = get_settings()
    login = request.login.strip()
    if not login:
        raise HTTPException(status_code=400, detail="Login is required")

    user = await uow.user_repo.get_by_admin_login(login)
    if (
        not user
        or not user.is_superuser
        or not user.admin_password_hash
        or not _password_service.verify_password(request.password, user.admin_password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    if not user.admin_require_telegram_2fa:
        access_token = _jwt_service.create_access_token(user.user_id)
        refresh_token = _jwt_service.create_refresh_token(user.user_id)
        return AuthStatusResponse(
            status="approved",
            access_token=access_token,
            refresh_token=refresh_token,
        )

    token = await _auth_repo.create_password_2fa_session(user.user_id)
    bot_username = await ensure_resolved_bot_username(settings)
    if not bot_username:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot username is not configured",
        )
    deep_link = f"https://t.me/{bot_username}?start=auth_{token}"
    return AuthStatusResponse(status="pending_2fa", token=token, deep_link=deep_link)


@router.post("/credentials/setup", response_model=BindAdminCredentialsResponse)
@router.post("/setup", response_model=BindAdminCredentialsResponse)
async def setup_admin_credentials(
    request: BindAdminCredentialsRequest,
    admin: User = Depends(get_current_admin),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
):
    settings = get_settings()
    login = request.login.strip()
    password = request.password

    if not login:
        raise HTTPException(status_code=400, detail="Login is required")
    if len(password) < settings.ADMIN_PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {settings.ADMIN_PASSWORD_MIN_LENGTH} characters",
        )

    existing_user = await uow.user_repo.get_by_admin_login(login)
    if existing_user and existing_user.user_id != admin.user_id:
        raise HTTPException(status_code=409, detail="Login is already taken")

    current_admin = await uow.user_repo.get(admin.user_id)
    if not current_admin:
        raise HTTPException(status_code=404, detail="User not found")
    if current_admin.admin_login and current_admin.admin_password_hash:
        raise HTTPException(status_code=409, detail="Credentials are already set")

    current_admin.admin_login = login
    current_admin.admin_password_hash = _password_service.hash_password(password)
    current_admin.admin_credentials_set_at = datetime.now(timezone.utc)
    await uow.user_repo.update(current_admin)
    await uow.commit()

    return BindAdminCredentialsResponse(status="ok")


@router.post("/credentials/bind", response_model=BindAdminCredentialsResponse)
async def bind_admin_credentials_legacy(
    request: BindAdminCredentialsRequest,
    admin: User = Depends(get_current_admin),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
):
    # Legacy alias kept for backward compatibility.
    return await setup_admin_credentials(request, admin, uow)


@router.post("/credentials/change-password", response_model=BindAdminCredentialsResponse)
async def change_admin_password(
    request: ChangePasswordRequest,
    admin: User = Depends(get_current_admin),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
):
    settings = get_settings()
    if len(request.new_password) < settings.ADMIN_PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {settings.ADMIN_PASSWORD_MIN_LENGTH} characters",
        )

    current_admin = await uow.user_repo.get(admin.user_id)
    if not current_admin or not current_admin.admin_password_hash:
        raise HTTPException(status_code=400, detail="Credentials are not set")
    if not _password_service.verify_password(request.current_password, current_admin.admin_password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    current_admin.admin_password_hash = _password_service.hash_password(request.new_password)
    await uow.user_repo.update(current_admin)
    await uow.commit()
    return BindAdminCredentialsResponse(status="ok")


@router.post("/credentials/toggle-2fa", response_model=BindAdminCredentialsResponse)
async def toggle_twofa(
    request: ToggleTwoFaRequest,
    admin: User = Depends(get_current_admin),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
):
    current_admin = await uow.user_repo.get(admin.user_id)
    if not current_admin:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_admin.admin_login or not current_admin.admin_password_hash:
        raise HTTPException(status_code=400, detail="Set login and password first")

    current_admin.admin_require_telegram_2fa = request.enabled
    await uow.user_repo.update(current_admin)
    await uow.commit()
    return BindAdminCredentialsResponse(status="ok")


@router.post("/init", response_model=InitAuthResponse)
async def init_auth():
    """
    Создает временную сессию (UUID) и возвращает deep link для перехода в Telegram бота.
    """
    settings = get_settings()
    token = await _auth_repo.create_auth_session()

    bot_username = await ensure_resolved_bot_username(settings)
    if not bot_username:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot username is not configured",
        )
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
    session_type = session.get("session_type", "qr_login")
    
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

    if status == "pending":
        if session_type == "password_2fa":
            return AuthStatusResponse(status="pending_2fa")
        return AuthStatusResponse(status="pending")

    return AuthStatusResponse(status=status) # rejected


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
