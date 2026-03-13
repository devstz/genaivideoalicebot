from typing import Any, Protocol


class BaseCacheProvider(Protocol):
    """
    Интерфейс для работы с кэшем (Redis, Memcached, Local Memory).
    """

    async def get(self, key: str) -> Any | None:
        """Получить значение по ключу."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        expires_in: int | None = None,
    ) -> None:
        """
        Сохранить значение по ключу.
        :param expires_in: Время жизни ключа в секундах (TTL).
        """
        ...

    async def delete(self, key: str) -> None:
        """Удалить значение по ключу."""
        ...

    async def exists(self, key: str) -> bool:
        """Проверить, существует ли ключ."""
        ...
