"""In-memory caching layer with TTL-based invalidation."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, Optional


@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    loading: bool = False


class DataCache:
    """Central async cache with TTL support.

    Usage:
        cache = DataCache()
        data = await cache.get("active_sessions", loader=read_sessions, ttl=2.0)
    """

    def __init__(self):
        self._entries: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(
        self,
        key: str,
        loader: Callable[[], Any],
        ttl: float = 30.0,
    ) -> Any:
        """Get cached value or call loader to refresh.

        Args:
            key: Cache key
            loader: Callable (sync or async) that returns the data
            ttl: Time-to-live in seconds
        """
        now = time.time()
        entry = self._entries.get(key)

        if entry and now < entry.expires_at and not entry.loading:
            return entry.value

        async with self._lock:
            # Double-check after acquiring lock
            entry = self._entries.get(key)
            if entry and now < entry.expires_at:
                return entry.value

            # Mark as loading
            if entry:
                entry.loading = True

            try:
                if asyncio.iscoroutinefunction(loader):
                    value = await loader()
                else:
                    loop = asyncio.get_event_loop()
                    value = await loop.run_in_executor(None, loader)

                self._entries[key] = CacheEntry(
                    value=value,
                    expires_at=now + ttl,
                    loading=False,
                )
                return value
            except Exception:
                # On error, keep stale value if available
                if entry:
                    entry.loading = False
                    return entry.value
                raise

    def invalidate(self, key: str) -> None:
        """Remove a specific cache entry."""
        self._entries.pop(key, None)

    def invalidate_all(self) -> None:
        """Clear all cached data."""
        self._entries.clear()

    def get_sync(self, key: str) -> Optional[Any]:
        """Get cached value synchronously without refreshing."""
        entry = self._entries.get(key)
        if entry and time.time() < entry.expires_at:
            return entry.value
        return None
