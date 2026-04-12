"""Simple command‑line wrapper for the locally running Ollama server.

Usage:
    python ollama_cli.py "<prompt>" [--model MODEL]

The script reads the OLLAMA_BASE_URL environment variable (default
http://127.0.0.1:9001) and prints the generated response to stdout.

It is deliberately lightweight and does not require any UI – ideal
for users with visual impairments who rely on screen‑readers or copy‑
paste workflows.
"""

import os
import sys
import argparse
import asyncio
import httpx

DEFAULT_MODEL = "llama3:8b"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:9001")

async def generate(prompt: str, model: str) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
    resp.raise_for_status()
    return resp.json().get("response", "")

def main() -> None:
    parser = argparse.ArgumentParser(description="Ollama CLI wrapper")
    parser.add_argument("prompt", help="Prompt text")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model identifier (default: %(default)s)")
    args = parser.parse_args()

    response = asyncio.run(generate(args.prompt, args.model))
    # Print without extra formatting – easy to pipe or copy‑paste.
    print(response)

if __name__ == "__main__":
    main()
