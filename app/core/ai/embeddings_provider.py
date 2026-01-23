import logging
import os
import re
import math
import hashlib
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Interface for embedding providers."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1/embeddings"

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI embeddings will not work")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        payload = {
            "model": self.model,
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("data", [])
            return [item.get("embedding", []) for item in items]


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embedding fallback (no external API)."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text or "") for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = re.findall(r"[\\w-]+", text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            idx = int(digest, 16) % self.dim
            vector[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector


def get_embedding_provider() -> EmbeddingProvider:
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("Using OpenAI embeddings")
        return OpenAIEmbeddingProvider(api_key=openai_key)
    logger.info("Using hash embeddings (fallback)")
    return HashEmbeddingProvider()
