"""
NVIDIA NIM Client — Llama 3.1 Integration
Handles API calls, JSON parsing, and retry logic.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Optional

import requests


# Expected keys in the LLM JSON response
PERSONA_KEYS = {"HypeBot", "CritiBot", "LurkerBot"}


class NIMClient:
    """
    Client for NVIDIA NIM inference endpoint.

    Set your API key via:
        export NVIDIA_API_KEY="nvapi-..."
    or pass it directly as `api_key`.

    Model default: meta/llama-3.1-8b-instruct (free tier)
    """

    DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"
    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.85,
        max_tokens: int = 256,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "NVIDIA API key required. Set NVIDIA_API_KEY env var or pass api_key=."
            )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        retries: int = 3,
    ) -> dict[str, str]:
        """
        Call the LLM and return parsed persona dict:
            {"HypeBot": "...", "CritiBot": "...", "LurkerBot": "..."}

        Retries on parse failure up to `retries` times with slight temperature bump.
        """
        for attempt in range(retries):
            temp = self.temperature + attempt * 0.05  # nudge on retry
            raw = self._call_api(system_prompt, user_prompt, temperature=temp)
            parsed = self._parse_json(raw)
            if parsed:
                return parsed
            # wait before retry
            time.sleep(1.0)

        # Last-resort fallback: return safe defaults so the UI doesn't crash
        return self._fallback_responses()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _call_api(
        self, system_prompt: str, user_prompt: str, temperature: float
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "top_p": 0.95,
        }
        resp = self._session.post(
            f"{self.BASE_URL}/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _parse_json(self, raw: str) -> Optional[dict[str, str]]:
        """
        Attempt to extract a valid JSON object from the raw LLM output.
        Handles cases where the model wraps the JSON in markdown fences.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()

        # Try direct parse first
        try:
            obj = json.loads(cleaned)
            if PERSONA_KEYS.issubset(obj.keys()):
                return {k: str(obj[k]) for k in PERSONA_KEYS}
        except json.JSONDecodeError:
            pass

        # Try to extract first {...} block
        match = re.search(r"\{[^{}]+\}", cleaned, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group())
                if PERSONA_KEYS.issubset(obj.keys()):
                    return {k: str(obj[k]) for k in PERSONA_KEYS}
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _fallback_responses() -> dict[str, str]:
        return {
            "HypeBot": "POGGERS",
            "CritiBot": "Interesting, let's see how this plays out.",
            "LurkerBot": ".",
        }

    def __repr__(self) -> str:
        return f"NIMClient(model={self.model}, temp={self.temperature})"
