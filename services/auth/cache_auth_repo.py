import uuid
from typing import Optional

from services.providers.cache.base_cache import BaseCacheProvider


class CacheAuthRepository:
    """
    Репозиторий для хранения временных кодов авторизации (auth_tokens) в In-Memory / Redis кэше.
    TTL по умолчанию = 5 минут (300 секунд).
    """

    def __init__(self, cache: BaseCacheProvider):
        self._cache = cache
        self.ttl_seconds = 300
        self.prefix = "auth_session:"

    def _make_key(self, token: str) -> str:
        return f"{self.prefix}{token}"

    async def _create_session(
        self,
        *,
        session_type: str,
        user_id: int | None = None,
    ) -> str:
        token = str(uuid.uuid4())
        key = self._make_key(token)
        session_data = {
            "status": "pending",
            "user_id": user_id,
            "session_type": session_type,
        }
        await self._cache.set(key, session_data, expires_in=self.ttl_seconds)
        return token

    async def create_auth_session(self) -> str:
        """
        Создает новую сессию ожидания авторизации и возвращает уникальный токен.
        Статус по умолчанию "pending".
        """
        return await self._create_session(session_type="qr_login")

    async def create_password_2fa_session(self, user_id: int) -> str:
        """
        Создает сессию подтверждения входа после успешной проверки login/password.
        """
        return await self._create_session(session_type="password_2fa", user_id=user_id)

    async def get_session(self, token: str) -> Optional[dict]:
        """
        Возвращает данные сессии. 
        """
        key = self._make_key(token)
        return await self._cache.get(key)

    async def approve_session(self, token: str, user_id: int) -> bool:
        """
        Одобряет сессию, привязывая её к user_id.
        Возвращает True если успешно, False если сессия не найдена/истекла.
        """
        key = self._make_key(token)
        session_data = await self._cache.get(key)
        if not session_data or session_data.get("status") != "pending":
            return False
            
        session_data["status"] = "approved"
        session_data["user_id"] = user_id
        
        # Обновляем кэш, оставляя старый TTL (для In-Memory придется просто обновить значение)
        await self._cache.set(key, session_data, expires_in=self.ttl_seconds)
        return True

    async def reject_session(self, token: str) -> bool:
        """
        Отклоняет сессию.
        """
        key = self._make_key(token)
        session_data = await self._cache.get(key)
        if not session_data or session_data.get("status") != "pending":
            return False
            
        session_data["status"] = "rejected"
        await self._cache.set(key, session_data, expires_in=self.ttl_seconds)
        return True

    async def delete_session(self, token: str) -> None:
        """
        Удаляет сессию (например, после успешной выдачи JWT).
        """
        key = self._make_key(token)
        await self._cache.delete(key)
