"""OpenAI‑compatible LLM client (for OpenRouter / NVIDIA GLM‑5)
Uses the official AsyncOpenAI SDK.  The SDK automatically appends
/v1/chat/completions to the base URL, so we keep the base URL as‑is.
"""
import os
from typing import Optional, List, Dict
from openai import AsyncOpenAI   # type: ignore
from openai import APIError      # type: ignore

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_client: Optional[AsyncOpenAI] = None

def _get_client() -> AsyncOpenAI:
    """Singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    return _client

async def generate(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Prompt‑only API (maps to a single‑message chat request)."""
    client = _get_client()
    model_name = model or os.getenv("OPENROUTER_MODEL", "glm-5b")
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except APIError as exc:   # pragma: no cover
        raise exc

async def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Full chat interface – forwards the list unchanged."""
    client = _get_client()
    model_name = model or os.getenv("OPENROUTER_MODEL", "glm-5b")
    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except APIError as exc:   # pragma: no cover
        raise exc
