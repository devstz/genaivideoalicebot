from sitapi.config import get_config
from sitapi.infra.providers.cache.redis import RedisCache

_cache_instance: RedisCache | None = None


def get_redis_cache() -> RedisCache:
    """Return a cached RedisCache instance configured via settings."""
    global _cache_instance
    if _cache_instance is None:
        cfg = get_config().REDIS
        db_index: int | None = None
        if cfg.db is not None:
            try:
                db_index = int(cfg.db)
            except (TypeError, ValueError):
                db_index = None
        _cache_instance = RedisCache(
            url=cfg.url,
            key_prefix=cfg.key_prefix,
            default_ttl_sec=cfg.ttl_seconds,
            db=db_index,
        )
    return _cache_instance


async def close_cache() -> None:
    global _cache_instance
    if _cache_instance is not None:
        await _cache_instance.close()
        _cache_instance = None


__all__ = ["close_cache", "get_redis_cache"]
