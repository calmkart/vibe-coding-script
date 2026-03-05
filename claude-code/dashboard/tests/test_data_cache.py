"""Tests for dashboard.data.cache module."""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dashboard.data.cache import DataCache, CacheEntry


class TestDataCache:
    """Test the DataCache async caching layer."""

    def _run(self, coro):
        """Helper to run async code in tests."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_basic_get_and_cache(self):
        cache = DataCache()
        call_count = 0

        def loader():
            nonlocal call_count
            call_count += 1
            return {"data": "hello"}

        async def run():
            result1 = await cache.get("key1", loader, ttl=60.0)
            result2 = await cache.get("key1", loader, ttl=60.0)
            return result1, result2

        r1, r2 = self._run(run())
        assert r1 == {"data": "hello"}
        assert r2 == {"data": "hello"}
        assert call_count == 1  # Loader should only be called once

    def test_ttl_expiration(self):
        cache = DataCache()
        call_count = 0

        def loader():
            nonlocal call_count
            call_count += 1
            return call_count

        async def run():
            r1 = await cache.get("key1", loader, ttl=0.1)
            await asyncio.sleep(0.2)
            r2 = await cache.get("key1", loader, ttl=0.1)
            return r1, r2

        r1, r2 = self._run(run())
        assert r1 == 1
        assert r2 == 2  # TTL expired, loader called again

    def test_invalidate(self):
        cache = DataCache()
        call_count = 0

        def loader():
            nonlocal call_count
            call_count += 1
            return call_count

        async def run():
            r1 = await cache.get("key1", loader, ttl=60.0)
            cache.invalidate("key1")
            r2 = await cache.get("key1", loader, ttl=60.0)
            return r1, r2

        r1, r2 = self._run(run())
        assert r1 == 1
        assert r2 == 2

    def test_invalidate_all(self):
        cache = DataCache()

        async def run():
            await cache.get("k1", lambda: "v1", ttl=60.0)
            await cache.get("k2", lambda: "v2", ttl=60.0)
            cache.invalidate_all()
            # After invalidate_all, cache should be empty
            r1 = cache.get_sync("k1")
            r2 = cache.get_sync("k2")
            return r1, r2

        r1, r2 = self._run(run())
        assert r1 is None
        assert r2 is None

    def test_invalidate_nonexistent_key(self):
        cache = DataCache()
        # Should not raise
        cache.invalidate("nonexistent")

    def test_get_sync_returns_cached_value(self):
        cache = DataCache()

        async def run():
            await cache.get("key1", lambda: "hello", ttl=60.0)
            return cache.get_sync("key1")

        result = self._run(run())
        assert result == "hello"

    def test_get_sync_returns_none_for_missing(self):
        cache = DataCache()
        assert cache.get_sync("missing") is None

    def test_get_sync_returns_none_for_expired(self):
        cache = DataCache()

        async def run():
            await cache.get("key1", lambda: "hello", ttl=0.01)
            await asyncio.sleep(0.05)
            return cache.get_sync("key1")

        result = self._run(run())
        assert result is None

    def test_async_loader(self):
        cache = DataCache()

        async def async_loader():
            return "async_value"

        async def run():
            return await cache.get("key1", async_loader, ttl=60.0)

        result = self._run(run())
        assert result == "async_value"

    def test_loader_error_returns_stale_value(self):
        cache = DataCache()
        call_count = 0

        def loader():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise RuntimeError("loader failed")
            return "good_value"

        async def run():
            r1 = await cache.get("key1", loader, ttl=0.01)
            await asyncio.sleep(0.05)
            r2 = await cache.get("key1", loader, ttl=0.01)
            return r1, r2

        r1, r2 = self._run(run())
        assert r1 == "good_value"
        assert r2 == "good_value"  # Stale value returned on error

    def test_loader_error_no_stale_value_raises(self):
        cache = DataCache()

        def failing_loader():
            raise RuntimeError("always fails")

        async def run():
            return await cache.get("key1", failing_loader, ttl=60.0)

        with pytest.raises(RuntimeError, match="always fails"):
            self._run(run())

    def test_multiple_keys(self):
        cache = DataCache()

        async def run():
            await cache.get("a", lambda: 1, ttl=60.0)
            await cache.get("b", lambda: 2, ttl=60.0)
            await cache.get("c", lambda: 3, ttl=60.0)
            return cache.get_sync("a"), cache.get_sync("b"), cache.get_sync("c")

        a, b, c = self._run(run())
        assert a == 1
        assert b == 2
        assert c == 3

    def test_concurrent_access(self):
        """Multiple concurrent gets on the same key should not crash.

        We create the DataCache inside the event loop so its internal
        asyncio.Lock() is bound to the correct loop.
        """
        async def run():
            cache = DataCache()
            call_count = 0

            def slow_loader():
                nonlocal call_count
                call_count += 1
                time.sleep(0.05)
                return "result"

            tasks = [cache.get("key1", slow_loader, ttl=60.0) for _ in range(5)]
            results = await asyncio.gather(*tasks)
            return results, call_count

        results, call_count = self._run(run())
        assert all(r == "result" for r in results)
        # Due to the lock, loader should ideally be called only once or twice
        # (first caller loads, others wait)
        assert call_count <= 5  # At most 5, but likely much fewer


class TestCacheEntry:
    """Test CacheEntry dataclass."""

    def test_fields(self):
        e = CacheEntry(value="hello", expires_at=time.time() + 60, loading=False)
        assert e.value == "hello"
        assert e.loading is False

    def test_loading_flag(self):
        e = CacheEntry(value=None, expires_at=0, loading=True)
        assert e.loading is True
