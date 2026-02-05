"""Search provider implementations."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Result from a search query."""

    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    """Protocol for search providers."""

    def get_provider_name(self) -> str:
        """Return the provider name."""
        ...

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Search for the given query."""
        ...

    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        ...


class TavilySearchProvider:
    """
    Tavily API search provider.

    Free tier: 1000 searches/month
    Environment variable: TAVILY_API_KEY
    """

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not set, search functionality will be limited")

    def get_provider_name(self) -> str:
        return "Tavily Search"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Search using Tavily API."""
        if not self.api_key:
            logger.warning("Tavily API key not configured, returning empty results")
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": num_results,
                        "search_depth": "advanced",
                        "include_raw_content": False,
                    },
                )

                if response.status_code == 401:
                    raise ValueError("Invalid Tavily API key")

                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("content") or item.get("snippet", ""),
                        )
                    )
                return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Tavily search HTTP error: {e}")
            raise ValueError(f"Tavily search failed: {e}")
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            raise ValueError(f"Tavily search failed: {e}")


class DummySearchProvider:
    """
    Dummy search provider for testing without API keys.

    Returns mock results for any query.
    """

    def get_provider_name(self) -> str:
        return "Dummy Search"

    def is_configured(self) -> bool:
        return True

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Return mock search results."""
        logger.info(f"Dummy search for: {query}")
        return [
            SearchResult(
                title=f"Mock Result {i+1} for '{query}'",
                url=f"https://example.com/result-{i+1}",
                snippet=f"This is a mock search result snippet for query: {query}. "
                "This would contain relevant content from the search results.",
            )
            for i in range(min(num_results, 3))
        ]


def get_search_provider() -> SearchProvider:
    """
    Get the configured search provider based on environment.

    Environment variable: SEARCH_PROVIDER
    - "tavily": Use Tavily API (requires TAVILY_API_KEY)
    - "dummy": Use dummy provider for testing
    """
    provider_name = os.getenv("SEARCH_PROVIDER", "dummy").lower()

    if provider_name == "tavily":
        provider = TavilySearchProvider()
        if provider.is_configured():
            return provider
        logger.warning("Tavily not configured, falling back to dummy provider")
        return DummySearchProvider()

    return DummySearchProvider()
