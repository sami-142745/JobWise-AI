import json
import logging
import re
import time
from typing import Any, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Raised when Ollama cannot be reached or returns an invalid response."""


def _balanced_block(text: str, open_ch: str, close_ch: str) -> str | None:
    """Return the outermost bracket-balanced substring, or None."""
    start = text.find(open_ch)
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _extract_json(raw: str) -> Any:
    """Robustly parse JSON out of a model response.

    Ollama may wrap the payload in markdown code fences, add prose before or
    after the JSON, or emit trailing commas. This helper isolates the largest
    top-level JSON object/array and decodes it.
    """
    if not raw:
        raise OllamaError("Empty response from model.")

    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Direct parse attempt first.
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fall back to the largest balanced object/array block.
    candidates = []
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        block = _balanced_block(text, open_ch, close_ch)
        if block is not None:
            candidates.append(block)
    if candidates:
        longest = max(candidates, key=len)
        try:
            return json.loads(longest)
        except (json.JSONDecodeError, TypeError):
            pass
    raise OllamaError("Model response did not contain valid JSON.")


class OllamaClient:
    """Minimal HTTP client for a local Ollama server.

    Designed to be fully testable: methods raise :class:`OllamaError` on any
    transport/parse failure, and :meth:`is_available` is cached for a short
    TTL so the app does not ping the server on every request.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        cache_ttl: int = 15,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = float(timeout or settings.OLLAMA_TIMEOUT)
        self.cache_ttl = cache_ttl
        self._available: Optional[bool] = None
        self._available_at: float = 0.0

    # ── Availability ────────────────────────────────────────────────────
    def available_models(self) -> list[str]:
        """List model names installed in Ollama. Raises OllamaError on failure."""
        try:
            with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(f"Ollama unavailable: {exc}") from exc
        models = data.get("models", []) if isinstance(data, dict) else []
        return [str(item.get("name", "")) for item in models if isinstance(item, dict)]

    def is_available(self) -> bool:
        """True if the configured model (or any model) is reachable. Cached."""
        now = time.monotonic()
        if self._available is not None and (now - self._available_at) < self.cache_ttl:
            return self._available
        try:
            models = self.available_models()
            self._available = bool(models)  # any installed model counts as online
            if self.model not in models:
                logger.info(
                    "Configured model '%s' not pulled yet; Ollama still reachable.", self.model
                )
        except OllamaError as exc:
            logger.info("Ollama not available: %s", exc)
            self._available = False
        self._available_at = now
        return self._available

    # ── Generation ──────────────────────────────────────────────────────
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_json: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """POST /api/generate and return the raw text response."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else settings.OLLAMA_TEMPERATURE,
                "num_predict": max_tokens if max_tokens is not None else settings.OLLAMA_MAX_TOKENS,
            },
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=httpx.Timeout(timeout or self.timeout)) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(f"Ollama generation failed: {exc}") from exc

        text = data.get("response", "") if isinstance(data, dict) else ""
        if not text.strip():
            raise OllamaError("Ollama returned an empty response.")
        return text

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Generate a response and decode it as JSON.

        Raises :class:`OllamaError` if the model output cannot be parsed as
        JSON, so callers can fall back to the offline agent.
        """
        raw = self.generate(
            prompt,
            system=system,
            format_json=True,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        return _extract_json(raw)


ollama_client = OllamaClient()