"""
RAG — Contextual Memory Module
Stores the accumulated stream transcription in a FAISS vector store
and retrieves the most relevant fragments before each LLM call.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class TranscriptChunk:
    text: str
    timestamp: float = field(default_factory=time.time)
    index: int = 0  # position in the session


class TranscriptionRAG:
    """
    Vector store for live stream transcription fragments.

    Usage:
        rag = TranscriptionRAG()
        rag.add("The streamer just picked up the sniper rifle")
        context = rag.retrieve("sniper", top_k=3)
    """

    MODEL_NAME = "all-MiniLM-L6-v2"  # fast, 384-dim, free

    def __init__(self, embedding_dim: int = 384):
        self.model = SentenceTransformer(self.MODEL_NAME)
        self.embedding_dim = embedding_dim

        # Flat inner-product index — exact search, good enough for <10k chunks
        self.index = faiss.IndexFlatIP(embedding_dim)

        self.chunks: list[TranscriptChunk] = []
        self._chunk_counter = 0

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def add(self, text: str) -> None:
        """Embed a new transcription chunk and add it to the FAISS index."""
        text = text.strip()
        if not text:
            return

        embedding = self._embed([text])  # (1, dim)
        # Normalize for cosine similarity via inner product
        faiss.normalize_L2(embedding)
        self.index.add(embedding)

        chunk = TranscriptChunk(text=text, index=self._chunk_counter)
        self.chunks.append(chunk)
        self._chunk_counter += 1

    def add_batch(self, texts: list[str]) -> None:
        """Batch-add multiple transcription segments."""
        texts = [t.strip() for t in texts if t.strip()]
        if not texts:
            return

        embeddings = self._embed(texts)  # (n, dim)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        for text in texts:
            self.chunks.append(TranscriptChunk(text=text, index=self._chunk_counter))
            self._chunk_counter += 1

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 3) -> list[TranscriptChunk]:
        """
        Return the top_k most semantically similar chunks to the query.
        Falls back gracefully when fewer chunks exist.
        """
        if self.index.ntotal == 0:
            return []

        top_k = min(top_k, self.index.ntotal)
        query_emb = self._embed([query])
        faiss.normalize_L2(query_emb)

        _scores, indices = self.index.search(query_emb, top_k)
        return [self.chunks[i] for i in indices[0] if i >= 0]

    def retrieve_text(self, query: str, top_k: int = 3) -> str:
        """Convenience: return retrieved chunks joined as a single string."""
        chunks = self.retrieve(query, top_k=top_k)
        return "\n".join(c.text for c in chunks)

    def get_recent(self, n: int = 5) -> list[TranscriptChunk]:
        """Return the n most recently added chunks (temporal context)."""
        return self.chunks[-n:]

    def get_recent_text(self, n: int = 5) -> str:
        chunks = self.get_recent(n)
        return "\n".join(c.text for c in chunks)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _embed(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.astype("float32")

    def __len__(self) -> int:
        return self.index.ntotal

    def __repr__(self) -> str:
        return f"TranscriptionRAG(chunks={len(self)}, model={self.MODEL_NAME})"
