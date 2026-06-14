"""Science AI Lab — 임베딩 (Ollama nomic-embed-text)

텍스트 → 768차원 벡터. Pi 5 로컬에서 동작, 인터넷 불필요.
"""

from __future__ import annotations

import os

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("SCIENCE_AI_EMBED_MODEL", "nomic-embed-text")


def embed(text: str) -> list[float] | None:
    if not text or not text.strip():
        return None
    try:
        r = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        r.raise_for_status()
        return r.json().get("embedding")
    except Exception:
        return None


def embed_batch(texts: list[str]) -> list[list[float] | None]:
    return [embed(t) for t in texts]
