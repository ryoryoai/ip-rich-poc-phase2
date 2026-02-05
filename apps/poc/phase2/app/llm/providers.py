"""LLM provider abstraction for OpenAI and Anthropic."""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from anthropic import Anthropic

from app.core import settings, get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM call."""

    content: str
    parsed_json: dict[str, Any] | None
    model: str
    tokens_input: int
    tokens_output: int
    latency_ms: int


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Call the LLM with the given prompts."""
        pass

    def _parse_json(self, content: str) -> dict[str, Any] | None:
        """Parse JSON from content, handling markdown code blocks."""
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response", content=content[:200])
            return None


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Call OpenAI API."""
        start_time = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        latency_ms = int((time.time() - start_time) * 1000)
        content = response.choices[0].message.content or ""

        return LLMResponse(
            content=content,
            parsed_json=self._parse_json(content),
            model=self.model,
            tokens_input=response.usage.prompt_tokens if response.usage else 0,
            tokens_output=response.usage.completion_tokens if response.usage else 0,
            latency_ms=latency_ms,
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Call Anthropic API."""
        start_time = time.time()

        # Add JSON instruction to system prompt for Claude
        json_system_prompt = f"{system_prompt}\n\nIMPORTANT: Respond with valid JSON only. No markdown, no explanations."

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=json_system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )

        latency_ms = int((time.time() - start_time) * 1000)
        content = response.content[0].text if response.content else ""

        return LLMResponse(
            content=content,
            parsed_json=self._parse_json(content),
            model=self.model,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            latency_ms=latency_ms,
        )


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    """Get the configured LLM provider instance."""
    provider = provider or settings.llm_provider

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
