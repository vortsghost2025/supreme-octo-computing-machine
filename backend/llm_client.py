import os
import asyncio
from typing import Optional

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL_DEFAULT = os.getenv("OLLAMA_MODEL_DEFAULT", "llama3:8b")

ALLOWED_MODELS = frozenset([
    "llama3:8b",
    "llama3.1:8b",
    "llama3.2:8b",
    "llama3:70b",
    "llama3.1:70b",
    "mistral",
    "codellama:7b",
    "codellama:13b",
    "phi3",
])

LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "1"))
_ollama_semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENCY)


class OllamaError(RuntimeError):
    pass


def _validate_model(model: str) -> str:
    if model not in ALLOWED_MODELS:
        raise OllamaError(f"Model '{model}' not allowed. Allowed: {', '.join(sorted(ALLOWED_MODELS))}")
    return model


async def generate(*, prompt: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
    """Generate a completion using Ollama /api/generate (non-streaming)."""
    if model is None:
        model = OLLAMA_MODEL_DEFAULT

    _validate_model(model)

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        async with _ollama_semaphore:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
    except httpx.ConnectError as e:
        raise OllamaError(f"Failed to connect to Ollama at {OLLAMA_BASE_URL}: {e}") from e
    except httpx.TimeoutException as e:
        raise OllamaError(f"Request to Ollama timed out: {e}") from e
    except httpx.HTTPStatusError as e:
        raise OllamaError(f"Ollama error {e.response.status_code}: {e.response.text}") from e

    if resp.status_code != 200:
        raise OllamaError(f"Ollama error {resp.status_code}: {resp.text}")

    data = resp.json()
    return str(data.get("response", ""))
