"""Кеш @username бота из Telegram getMe на весь процесс; fallback — BOT_USERNAME из .env."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_UNSET: Any = object()
_cache: Any = _UNSET
_lock = asyncio.Lock()


def _env_fallback(settings: Any) -> Optional[str]:
    raw = (settings.BOT_USERNAME or "").strip().replace("@", "")
    return raw or None


async def ensure_resolved_bot_username(settings: Any) -> Optional[str]:
    """
    Один запрос getMe на процесс; дальше из кеша.
    При ошибке getMe — BOT_USERNAME из окружения.
    """
    global _cache
    if _cache is not _UNSET:
        return _cache  # type: ignore[return-value]

    async with _lock:
        if _cache is not _UNSET:
            return _cache  # type: ignore[return-value]

        token = (settings.TOKEN or "").strip()
        if token and token != "TOKEN":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                    data = r.json()
                if data.get("ok") and isinstance(data.get("result"), dict):
                    u = data["result"].get("username")
                    if isinstance(u, str) and u.strip():
                        _cache = u.strip().lstrip("@")
                        logger.info("Cached bot username from getMe: %s", _cache)
                        return _cache
            except Exception as e:
                logger.warning("getMe failed, using BOT_USERNAME fallback: %s", e)

        _cache = _env_fallback(settings)
        if _cache:
            logger.info("Using BOT_USERNAME from env: %s", _cache)
        else:
            logger.warning("Bot username unavailable (getMe failed and BOT_USERNAME empty)")
        return _cache


def get_bot_username_sync(settings: Any) -> Optional[str]:
    """Синхронно: кеш после ensure, иначе только BOT_USERNAME без HTTP."""
    if _cache is not _UNSET:
        return _cache  # type: ignore[return-value]
    return _env_fallback(settings)
