"""In-memory TTL cache for JP Index."""

from __future__ import annotations

import threading
import time
from typing import Any, Optional

from app.core import settings


class TTLCache:
    """Simple TTL cache with max entries."""

    def __init__(self, ttl_seconds: int, max_entries: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if self.ttl_seconds <= 0 or self.max_entries <= 0:
            return None
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        if self.ttl_seconds <= 0 or self.max_entries <= 0:
            return
        now = time.time()
        expires_at = now + self.ttl_seconds
        with self._lock:
            if len(self._store) >= self.max_entries:
                self._evict_one()
            self._store[key] = (expires_at, value)

    def _evict_one(self) -> None:
        # Remove the oldest expired entry, else arbitrary oldest
        if not self._store:
            return
        now = time.time()
        expired_keys = [k for k, (exp, _) in self._store.items() if exp < now]
        if expired_keys:
            for k in expired_keys:
                self._store.pop(k, None)
            return
        # Fallback: remove first inserted (not strict LRU)
        first_key = next(iter(self._store))
        self._store.pop(first_key, None)


search_cache = TTLCache(
    ttl_seconds=settings.jp_index_cache_ttl_seconds,
    max_entries=settings.jp_index_cache_max_entries,
)

resolve_cache = TTLCache(
    ttl_seconds=settings.jp_index_cache_ttl_seconds,
    max_entries=settings.jp_index_cache_max_entries,
)

changes_cache = TTLCache(
    ttl_seconds=settings.jp_index_cache_ttl_seconds,
    max_entries=settings.jp_index_cache_max_entries,
)
