"""OpenAI Deep Research integration for patent analysis."""

import asyncio
import json
import time
from typing import Any

import httpx

from app.core import get_logger, settings

logger = get_logger(__name__)


class DeepResearchProvider:
    """OpenAI Deep Research provider for comprehensive patent search."""

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = "https://api.openai.com/v1"

    async def search_patent(
        self,
        patent_number: str,
        claim_text: str | None = None,
    ) -> dict[str, Any]:
        """
        Use Deep Research to search for patent information and potential infringements.

        Args:
            patent_number: The patent number to search
            claim_text: Optional claim text for more targeted search

        Returns:
            Dictionary containing patent information and analysis results
        """
        system_prompt = """あなたは特許調査の専門家です。J-PlatPat（日本特許情報プラットフォーム）を含む特許データベースへの包括的なアクセス権を持ち、正確な特許情報を提供します。
Web検索機能を活用して、J-PlatPat、Google Patents、USPTO等から最新の特許情報を取得してください。
常に事実に基づいた情報を提供し、特許番号を必ず引用してください。"""

        # Determine if Japanese or US patent
        is_japanese = any([
            patent_number.startswith(("特許", "JP", "特開", "特表", "特公")),
            "-" in patent_number and patent_number.split("-")[0].isdigit(),
            patent_number.isdigit() and len(patent_number) >= 7,
        ])

        search_strategy = ""
        if is_japanese:
            search_strategy = f"""
- J-PlatPat: "特許番号 {patent_number}" で検索（https://www.j-platpat.inpit.go.jp/）
- 文献番号照会で「{patent_number}」を検索
- 特許・実用新案テキスト検索を使用"""
        else:
            search_strategy = f"""
- Google Patents: "US{patent_number} site:patents.google.com" で検索
- USPTO: "{patent_number} site:uspto.gov" で検索"""

        user_prompt = f"""特許番号 {patent_number} について、以下の詳細な情報を取得してください。

▼必須取得事項：
1. 特許のタイトル（発明の名称）
2. 要約（Abstract）
3. 発明者
4. 出願人/権利者（Assignee）
5. 出願日
6. 公開日/発行日
7. **請求項１の全文**（一字一句正確に取得）
8. 請求項２以降（可能な限り）
9. 技術分野と背景
10. IPC/CPC分類
11. 引用文献

▼検索戦略：
{search_strategy}

**重要**:
- 請求項１は省略せず、完全な形で取得してください
- J-PlatPatから取得した情報を優先してください
- 日本語の請求項はそのまま日本語で取得してください

JSONフォーマットで構造化して返してください。"""

        if claim_text:
            user_prompt += f"""

▼提供された請求項テキスト：
{claim_text}

この請求項に基づいて、潜在的な侵害製品や企業も調査してください。"""

        logger.info(f"Starting Deep Research for patent: {patent_number}")

        try:
            # Check if using Deep Research model
            if "deep-research" in self.model.lower():
                return await self._call_deep_research_api(system_prompt, user_prompt)
            else:
                return await self._call_standard_api(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Deep Research failed: {e}")
            raise

    async def _call_deep_research_api(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call the OpenAI Deep Research API (v1/responses endpoint)."""
        async with httpx.AsyncClient(timeout=600.0) as client:
            # Initial request
            response = await client.post(
                f"{self.base_url}/responses",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": self.model,
                    "input": f"{system_prompt}\n\n{user_prompt}",
                    "reasoning": {"summary": "auto"},
                    "background": True,
                    "tools": [{"type": "web_search_preview"}],
                    "max_output_tokens": 10000,
                },
            )

            if response.status_code != 200:
                logger.error(f"Deep Research API error: {response.text}")
                # Fallback to standard API
                return await self._call_standard_api(system_prompt, user_prompt)

            data = response.json()
            logger.info(f"Deep Research initial response: {data.get('status')}")

            # Poll for completion if background processing
            if data.get("status") in ("queued", "in_progress"):
                response_id = data["id"]
                max_attempts = 90  # 15 minutes (10 second intervals)

                for attempt in range(max_attempts):
                    await asyncio.sleep(10)

                    poll_response = await client.get(
                        f"{self.base_url}/responses/{response_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )

                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        status = poll_data.get("status")

                        if attempt % 6 == 0:  # Log every minute
                            logger.info(
                                f"Deep Research progress: {status} ({(attempt + 1) * 10}s elapsed)"
                            )

                        if status == "completed":
                            return self._extract_response(poll_data)
                        elif status == "failed":
                            raise Exception(f"Deep Research failed: {poll_data.get('error')}")

                raise Exception("Deep Research timeout")
            else:
                return self._extract_response(data)

    async def _call_standard_api(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call the standard OpenAI Chat API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"},
                },
            )

            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_response": content}

    def _extract_response(self, data: dict) -> dict[str, Any]:
        """Extract the response content from Deep Research output."""
        output = data.get("output", [])
        if isinstance(output, list) and output:
            first_output = output[0]
            if first_output.get("type") == "message":
                content = first_output.get("content", [])
                if isinstance(content, list):
                    text = "".join(c.get("text", "") for c in content)
                else:
                    text = str(content)

                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw_response": text}

        return {"raw_response": json.dumps(data)}


class DeepResearchJobManager:
    """Manages Deep Research jobs with background processing."""

    def __init__(self):
        self.provider = DeepResearchProvider()

    async def start_research(
        self,
        job_id: str,
        patent_number: str,
        claim_text: str | None = None,
    ) -> dict[str, Any]:
        """
        Start a Deep Research job.

        Returns the research results or raises an exception.
        """
        try:
            result = await self.provider.search_patent(patent_number, claim_text)
            return {
                "job_id": job_id,
                "status": "completed",
                "result": result,
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
            }
