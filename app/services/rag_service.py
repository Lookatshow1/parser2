import math
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.ai.embeddings_provider import get_embedding_provider, HashEmbeddingProvider
from app.db.models_rag import RagDocument, RagChunk


class RagService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def ingest_text(
        self,
        *,
        organization_id: int,
        source_type: str,
        text: str,
        title: str | None = None,
        url: str | None = None,
        source_id: int | None = None,
        meta: dict | None = None,
    ) -> RagDocument:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("Empty text")

        meta_json = meta or {}
        existing = None
        if source_id is not None:
            existing = (
                self.db.query(RagDocument)
                .filter(
                    RagDocument.organization_id == organization_id,
                    RagDocument.source_type == source_type,
                    RagDocument.source_id == source_id,
                )
                .first()
            )
        if existing is None and url:
            existing = (
                self.db.query(RagDocument)
                .filter(
                    RagDocument.organization_id == organization_id,
                    RagDocument.source_type == source_type,
                    RagDocument.url == url,
                )
                .first()
            )

        if existing:
            self.db.query(RagChunk).filter(RagChunk.document_id == existing.id).delete()
            existing.title = title or existing.title
            existing.url = url or existing.url
            existing.raw_text = cleaned
            existing.meta_json = meta_json
            doc = existing
        else:
            doc = RagDocument(
                organization_id=organization_id,
                source_type=source_type,
                source_id=source_id,
                title=title,
                url=url,
                raw_text=cleaned,
                meta_json=meta_json,
                status="ready",
            )
            self.db.add(doc)
            self.db.flush()

        chunks = self._chunk_text(cleaned)
        try:
            embeddings = await self.embedding_provider.embed_texts([item["text"] for item in chunks])
        except Exception:
            fallback = HashEmbeddingProvider()
            embeddings = await fallback.embed_texts([item["text"] for item in chunks])

        for idx, chunk in enumerate(chunks):
            embedding = embeddings[idx] if idx < len(embeddings) else []
            self.db.add(
                RagChunk(
                    organization_id=organization_id,
                    document_id=doc.id,
                    chunk_index=chunk["index"],
                    content=chunk["text"],
                    embedding_json=embedding,
                    token_count=chunk["token_count"],
                )
            )

        self.db.commit()
        self.db.refresh(doc)
        return doc

    async def search(
        self,
        *,
        organization_id: int,
        query: str,
        top_k: int = 5,
        source_types: list[str] | None = None,
        limit_chunks: int = 500,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        try:
            query_embedding = await self.embedding_provider.embed_texts([query])
        except Exception:
            fallback = HashEmbeddingProvider()
            query_embedding = await fallback.embed_texts([query])
        qvec = query_embedding[0] if query_embedding else []
        if not qvec:
            return []

        q = (
            self.db.query(RagChunk, RagDocument)
            .join(RagDocument, RagChunk.document_id == RagDocument.id)
            .filter(RagChunk.organization_id == organization_id)
        )
        if source_types:
            q = q.filter(RagDocument.source_type.in_(source_types))

        rows = q.limit(limit_chunks).all()
        scored: list[dict[str, Any]] = []
        for chunk, doc in rows:
            score = self._cosine_similarity(qvec, chunk.embedding_json or [])
            if score <= 0:
                continue
            scored.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "score": score,
                    "text": chunk.content,
                    "source_type": doc.source_type,
                    "title": doc.title,
                    "url": doc.url,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[: max(1, top_k)]

    def _chunk_text(self, text: str, *, chunk_size: int = 220, overlap: int = 40) -> list[dict[str, Any]]:
        words = re.split(r"\s+", text)
        words = [w for w in words if w]
        if not words:
            return []
        chunk_size = max(50, chunk_size)
        overlap = min(overlap, chunk_size - 1)

        chunks: list[dict[str, Any]] = []
        start = 0
        index = 0
        while start < len(words):
            end = min(len(words), start + chunk_size)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            chunks.append(
                {
                    "index": index,
                    "text": chunk_text,
                    "token_count": len(chunk_words),
                }
            )
            index += 1
            if end >= len(words):
                break
            start = end - overlap
        return chunks

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        length = min(len(vec_a), len(vec_b))
        dot = sum(vec_a[i] * vec_b[i] for i in range(length))
        norm_a = math.sqrt(sum(vec_a[i] * vec_a[i] for i in range(length)))
        norm_b = math.sqrt(sum(vec_b[i] * vec_b[i] for i in range(length)))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
