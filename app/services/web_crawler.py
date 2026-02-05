"""Simple web crawler with robots.txt compliance and rate limiting."""

from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import httpx

from app.core import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    content: bytes


class RobotsCache:
    """Cache robots.txt per domain."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._parsers:
            robots_url = urljoin(base, "/robots.txt")
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                parser.read()
            except Exception:  # noqa: BLE001
                logger.warning("Failed to read robots.txt", robots_url=robots_url)
                parser = RobotFileParser()
                parser.parse("")
            self._parsers[base] = parser
        return self._parsers[base].can_fetch(self.user_agent, url)


class WebCrawler:
    """HTTP fetcher with robots and per-domain rate limit."""

    def __init__(
        self,
        user_agent: str | None = None,
        rate_limit_per_minute: int = 30,
        respect_robots: bool = True,
    ) -> None:
        self.user_agent = user_agent or settings.collection_user_agent
        self.rate_limit_per_minute = rate_limit_per_minute
        self.respect_robots = respect_robots
        self._last_request_at: dict[str, float] = {}
        self._robots = RobotsCache(self.user_agent)

    def _throttle(self, netloc: str) -> None:
        if self.rate_limit_per_minute <= 0:
            return
        min_interval = 60.0 / self.rate_limit_per_minute
        last = self._last_request_at.get(netloc)
        if last is None:
            return
        wait_time = min_interval - (time.time() - last)
        if wait_time > 0:
            time.sleep(wait_time)

    def fetch(self, url: str) -> FetchResult:
        parsed = urlparse(url)
        if self.respect_robots and not self._robots.allowed(url):
            raise PermissionError("Blocked by robots.txt")

        self._throttle(parsed.netloc)
        headers = {"User-Agent": self.user_agent}
        response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        self._last_request_at[parsed.netloc] = time.time()

        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        return FetchResult(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            content_type=content_type,
            content=response.content,
        )
