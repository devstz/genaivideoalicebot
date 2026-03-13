import asyncio
import time
from typing import Any

from .base_cache import BaseCacheProvider


class MockCacheProvider(BaseCacheProvider):
    """
    In-memory реализация кэша для локальной разработки.
    Хранит данные в обычном словаре `dict` и проверяет TTL (время жизни) при запросе.
    Автоматически очищать просроченные ключи мы не будем ради простоты,
    они просто "протухают" при попытке чтения.
    """

    def __init__(self):
        # Структура: {"key": {"value": Any, "expires_at": int | None}}
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def _is_expired(self, key: str) -> bool:
        """Проверяет, истек ли срок действия ключа. Если да - удаляет его."""
        item = self._store.get(key)
        if not item:
            return True

        expires_at = item.get("expires_at")
        if expires_at is not None and time.time() > expires_at:
            await self.delete(key) # Lazy eviction
            return True
            
        return False

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if await self._is_expired(key):
                return None
            return self._store[key]["value"]

    async def set(self, key: str, value: Any, expires_in: int | None = None) -> None:
        async with self._lock:
            expires_at = time.time() + expires_in if expires_in else None
            self._store[key] = {
                "value": value,
                "expires_at": expires_at
            }

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        async with self._lock:
            return not await self._is_expired(key)
