"""Simple in-memory rate limiter."""

from __future__ import annotations

import threading
import time
from typing import Optional

from app.core import settings


class RateLimiter:
    """Fixed-window rate limiter (per minute)."""

    def __init__(self, limit_per_minute: int) -> None:
        self.limit = limit_per_minute
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[int, int]] = {}

    def check(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        window = int(time.time() // 60)
        with self._lock:
            current = self._buckets.get(key)
            if not current or current[0] != window:
                self._buckets[key] = (window, 1)
                return True
            _, count = current
            if count >= self.limit:
                return False
            self._buckets[key] = (window, count + 1)
            return True


rate_limiter = RateLimiter(settings.jp_index_rate_limit_per_minute)


def rate_limit_key(client_ip: Optional[str], action: str) -> str:
    ip = client_ip or "unknown"
    return f"{action}:{ip}"
