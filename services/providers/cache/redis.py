import asyncio
import random
from collections.abc import Awaitable, Callable, Iterable
from typing import ParamSpec, TypeVar

from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from sitapi.domain.interfaces.cache import AsyncCachePort

T = TypeVar("T")
P = ParamSpec("P")


def _is_transient(exc: BaseException) -> bool:
    return isinstance(exc, (RedisTimeoutError, RedisConnectionError))


def with_retries(
    attempts: int = 3,
    base_delay: float = 0.05,
    max_delay: float = 0.5,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    def deco(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapped(*args, **kwargs) -> T:
            last_exc: BaseException | None = None
            for i in range(1, attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except BaseException as e:  # noqa: BLE001
                    if not _is_transient(e) or i == attempts:
                        raise
                    last_exc = e
                    delay = min(max_delay, base_delay * (2 ** (i - 1)))
                    delay *= random.uniform(0.5, 1.5)
                    await asyncio.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapped

    return deco


class RedisCache(AsyncCachePort):
    _INCR_WITH_TTL_LUA = """
local key = KEYS[1]
local amount = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
local exists = redis.call('EXISTS', key)

local newval = redis.call('INCRBY', key, amount)

if exists == 0 and ttl and ttl > 0 then
    redis.call('EXPIRE', key, ttl)
end

return newval
    """.strip()

    def __init__(
        self,
        url: str | None = None,
        *,
        key_prefix: str = "",
        default_ttl_sec: int | None = None,
        connect_timeout: float = 5.0,
        socket_timeout: float = 2.0,
        health_check_interval: int = 30,
        max_retries_per_call: int = 3,
        db: int | None = None,
    ) -> None:
        self._url = url
        if not self._url:
            raise ValueError("Redis URL must be provided")
        if not self._url.startswith("rediss://"):
            raise ValueError("Redis URL must use TLS (rediss://)")

        self._prefix: str = key_prefix
        self._default_ttl: int | None = default_ttl_sec
        self._max_retries: int = max(1, int(max_retries_per_call))

        self._r: Redis = Redis.from_url(
            self._url,
            db=db,
            socket_connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            health_check_interval=health_check_interval,
            retry_on_error=[RedisTimeoutError, RedisConnectionError],
            decode_responses=False,
        )

        self._incr_script: Callable[..., Awaitable[int]] = self._r.register_script(
            self._INCR_WITH_TTL_LUA
        )  # type: ignore[assignment]

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}" if self._prefix else key

    async def _run_with_retries(
        self, fn: Callable[P, Awaitable[T]], *args: P.args, **kwargs: P.kwargs
    ) -> T:
        last_exc: BaseException | None = None
        for i in range(1, self._max_retries + 1):
            try:
                return await fn(*args, **kwargs)
            except BaseException as e:
                if not _is_transient(e) or i == self._max_retries:
                    raise
                last_exc = e
                delay: float = min(0.5, 0.05 * (2 ** (i - 1))) * random.uniform(0.5, 1.5)
                await asyncio.sleep(delay)
        assert last_exc is not None
        raise last_exc

    async def get(self, key: str) -> bytes | None:
        return await self._run_with_retries(self._r.get, self._k(key))

    async def set(
        self, key: str, value: bytes, ttl_sec: int | None = None, nx: bool = False
    ) -> bool:
        ex: int | None = ttl_sec if ttl_sec is not None else self._default_ttl
        res: bool | None = await self._run_with_retries(
            self._r.set, self._k(key), value, ex=ex, nx=nx
        )
        return bool(res)

    async def mget(self, keys: Iterable[str]) -> list[bytes | None]:
        ks = [self._k(k) for k in keys]
        vals = await self._run_with_retries(self._r.mget, ks)
        return list(vals)

    async def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        count: int = await self._run_with_retries(
            self._r.delete, *[self._k(k) for k in keys]
        )
        return count

    async def expire(self, key: str, ttl_sec: int) -> bool:
        return bool(await self._run_with_retries(self._r.expire, self._k(key), ttl_sec))

    async def ttl(self, key: str) -> int | None:
        t: int | None = await self._run_with_retries(self._r.ttl, self._k(key))
        if t is None:
            return None
        if t < 0:
            return None if t == -2 else -1
        return int(t)

    async def incr(
        self, key: str, amount: int = 1, ttl_on_create: int | None = None
    ) -> int:
        args = [amount, ttl_on_create or 0]
        res: int = await self._run_with_retries(
            self._incr_script, keys=[self._k(key)], args=args
        )
        return int(res)

    async def ping(self) -> bool:
        try:
            ok: bool = await self._r.ping()  # type: ignore
            return ok
        except (RedisTimeoutError, RedisConnectionError):
            return False

    async def close(self) -> None:
        await self._r.aclose(close_connection_pool=True)

    def pipeline(self) -> Pipeline:
        return self._r.pipeline()

    async def zadd(
        self,
        key: str,
        mapping: dict[bytes | str, float | int],
        ttl_sec: int | None = None,
    ) -> int:
        result: int = await self._run_with_retries(self._r.zadd, self._k(key), mapping)
        if ttl_sec is not None and result > 0:
            await self.expire(key, ttl_sec)
        return int(result)

    async def zrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
        withscores: bool = False,
        desc: bool = False,
    ) -> list[bytes] | list[tuple[bytes, float]]:
        if desc:
            return await self._run_with_retries(
                self._r.zrevrange, self._k(key), start, end, withscores=withscores
            )
        return await self._run_with_retries(
            self._r.zrange, self._k(key), start, end, withscores=withscores
        )

    async def zcard(self, key: str) -> int:
        result: int = await self._run_with_retries(self._r.zcard, self._k(key))
        return int(result) if result is not None else 0
