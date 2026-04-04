import os
import asyncio
from typing import Optional

import httpx

# Ollama base URL as seen from the backend container/process.
# Typical local default: http://127.0.0.1:11434
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# Concurrency guard for GPU/model access.
# 1 = fully serialized access. Increase carefully.
LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "1"))
_ollama_semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENCY)


class OllamaError(RuntimeError):
    pass


async def generate(*, prompt: str, model: str = "llama3:8b", system: Optional[str] = None) -> str:
    """Generate a completion using Ollama /api/generate (non-streaming)."""
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    async with _ollama_semaphore:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)

    if resp.status_code != 200:
        raise OllamaError(f"Ollama error {resp.status_code}: {resp.text}")

    data = resp.json()
    return str(data.get("response", ""))
