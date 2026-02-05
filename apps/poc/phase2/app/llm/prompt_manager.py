"""Prompt management for loading and rendering prompts."""

import re
from pathlib import Path
from typing import Any

import yaml

from app.core import settings, get_logger

logger = get_logger(__name__)


class PromptManager:
    """Manages loading and rendering of prompt templates."""

    def __init__(self, prompts_dir: Path | None = None):
        self.prompts_dir = prompts_dir or settings.prompts_dir
        self._cache: dict[str, dict[str, Any]] = {}
        self._common_system_prompt: str | None = None

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_common_system_prompt(self) -> str:
        """Get the common system prompt."""
        if self._common_system_prompt is None:
            path = self.prompts_dir / "00_common_system_prompt.yaml"
            if path.exists():
                data = self._load_yaml(path)
                self._common_system_prompt = data.get("content", "")
            else:
                # Fallback to txt file
                txt_path = self.prompts_dir / "00_common_system_prompt.txt"
                if txt_path.exists():
                    self._common_system_prompt = txt_path.read_text(encoding="utf-8")
                else:
                    self._common_system_prompt = ""
        return self._common_system_prompt

    def load_prompt(self, prompt_id: str) -> dict[str, Any]:
        """
        Load a prompt by ID.

        Args:
            prompt_id: Prompt identifier (e.g., "01_fetch_planner", "10_claim_element_extractor")

        Returns:
            Prompt configuration dict with 'system_prompt', 'user_prompt', etc.
        """
        if prompt_id in self._cache:
            return self._cache[prompt_id]

        # Determine directory based on prompt number
        num = int(prompt_id.split("_")[0])
        if 1 <= num <= 7:
            subdir = "a_fetch_store_normalize"
        elif 8 <= num <= 9:
            subdir = "b_discovery"
        elif 10 <= num <= 16:
            subdir = "c_analyze"
        else:
            raise ValueError(f"Unknown prompt ID range: {prompt_id}")

        path = self.prompts_dir / subdir / f"{prompt_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        data = self._load_yaml(path)
        self._cache[prompt_id] = data
        return data

    def render(
        self,
        prompt_id: str,
        variables: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Render a prompt with variables.

        Args:
            prompt_id: Prompt identifier
            variables: Dictionary of variables to substitute

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        prompt_config = self.load_prompt(prompt_id)

        # Get base prompts
        system_prompt = prompt_config.get("system_prompt", "")
        user_prompt = prompt_config.get("user_prompt", "")

        # Add common system prompt if referenced
        if "{{common_system_prompt}}" in system_prompt:
            common = self.get_common_system_prompt()
            system_prompt = system_prompt.replace("{{common_system_prompt}}", common)

        # Render variables using {{variable}} syntax
        all_vars = {**variables}
        for key, value in all_vars.items():
            placeholder = "{{" + key + "}}"
            str_value = self._to_string(value)
            system_prompt = system_prompt.replace(placeholder, str_value)
            user_prompt = user_prompt.replace(placeholder, str_value)

        # Check for unrendered placeholders
        unrendered = set(re.findall(r"\{\{(\w+)\}\}", user_prompt))
        if unrendered:
            logger.warning(
                "Unrendered placeholders in prompt",
                prompt_id=prompt_id,
                placeholders=list(unrendered),
            )

        return system_prompt, user_prompt

    def _to_string(self, value: Any) -> str:
        """Convert a value to string for template substitution."""
        if value is None:
            return "null"
        if isinstance(value, (dict, list)):
            import json
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def list_prompts(self) -> list[dict[str, str]]:
        """List all available prompts."""
        prompts = []
        for subdir in ["a_fetch_store_normalize", "b_discovery", "c_analyze"]:
            dir_path = self.prompts_dir / subdir
            if dir_path.exists():
                for yaml_file in sorted(dir_path.glob("*.yaml")):
                    prompt_id = yaml_file.stem
                    try:
                        data = self.load_prompt(prompt_id)
                        prompts.append({
                            "id": prompt_id,
                            "name": data.get("name", prompt_id),
                            "description": data.get("description", ""),
                            "pipeline": subdir[0].upper(),  # A, B, or C
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load prompt {prompt_id}: {e}")
        return prompts
