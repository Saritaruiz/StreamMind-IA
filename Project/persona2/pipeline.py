"""
RAG-LLM Pipeline — Persona 2 Orchestrator
Ties together: TranscriptionRAG + prompt builders + NIMClient + delays.
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .llm import NIMClient
from .prompts import build_system_prompt, build_user_prompt
from .rag import TranscriptionRAG


# Delay config (seconds): simulates independent viewer arrival times
DELAY_CONFIG: dict[str, tuple[float, float]] = {
    "HypeBot":   (0.5, 2.0),   # reacts fast
    "CritiBot":  (2.0, 5.0),   # thinks before typing
    "LurkerBot": (4.0, 9.0),   # lurks, posts last
}


@dataclass
class ChatMessage:
    persona: str
    text: str
    delay: float      # seconds after LLM response to post
    timestamp: float  # absolute time.time() when posted


class RAGLLMPipeline:
    """
    Main pipeline for Persona 2.

    Workflow per streamer utterance:
        1. Add utterance to RAG store
        2. Retrieve relevant context (semantic + recent)
        3. Build prompts
        4. Call LLM → parse JSON
        5. Schedule messages with per-persona delays
        6. Yield ChatMessage objects as they become due

    Usage (sync):
        pipeline = RAGLLMPipeline(api_key="nvapi-...", stream_category="gaming")
        for msg in pipeline.process("I just got the sniper!"):
            print(f"[{msg.persona}] {msg.text}")

    Usage (async):
        async for msg in pipeline.aprocess("I just got the sniper!"):
            print(f"[{msg.persona}] {msg.text}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        stream_category: str = "gaming",
        top_k_semantic: int = 3,
        top_k_recent: int = 4,
        on_message: Optional[Callable[[ChatMessage], None]] = None,
    ):
        self.rag = TranscriptionRAG()
        self.llm = NIMClient(api_key=api_key)
        self.stream_category = stream_category
        self.top_k_semantic = top_k_semantic
        self.top_k_recent = top_k_recent
        self.on_message = on_message  # optional callback (for Gradio integration)

        # Pre-build system prompt — only changes when category changes
        self._system_prompt = build_system_prompt(stream_category)

    # ------------------------------------------------------------------
    # Category switching (called by Gradio if user changes category)
    # ------------------------------------------------------------------

    def set_category(self, category: str) -> None:
        self.stream_category = category
        self._system_prompt = build_system_prompt(category)

    # ------------------------------------------------------------------
    # Sync interface
    # ------------------------------------------------------------------

    def process(self, utterance: str) -> list[ChatMessage]:
        """
        Process one streamer utterance.
        Blocks until all messages have been delivered (respecting delays).
        Returns messages in delivery order.
        """
        responses = self._generate(utterance)
        scheduled = self._schedule(responses)
        delivered: list[ChatMessage] = []

        start = time.time()
        for msg in scheduled:
            wait = msg.delay - (time.time() - start)
            if wait > 0:
                time.sleep(wait)
            msg.timestamp = time.time()
            if self.on_message:
                self.on_message(msg)
            delivered.append(msg)

        return delivered

    # ------------------------------------------------------------------
    # Async interface (preferred for Gradio)
    # ------------------------------------------------------------------

    async def aprocess(self, utterance: str):
        """
        Async generator: yields ChatMessage objects as delays expire.
        Use with `async for msg in pipeline.aprocess(utterance)`.
        """
        loop = asyncio.get_event_loop()
        # Run blocking LLM call in thread pool so we don't block the event loop
        responses = await loop.run_in_executor(None, self._generate, utterance)
        scheduled = self._schedule(responses)

        start = time.monotonic()
        for msg in scheduled:
            wait = msg.delay - (time.monotonic() - start)
            if wait > 0:
                await asyncio.sleep(wait)
            msg.timestamp = time.time()
            if self.on_message:
                self.on_message(msg)
            yield msg

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _generate(self, utterance: str) -> dict[str, str]:
        """Add utterance to RAG, build prompts, call LLM."""
        self.rag.add(utterance)

        recent_ctx = self.rag.get_recent_text(n=self.top_k_recent)
        semantic_ctx = self.rag.retrieve_text(utterance, top_k=self.top_k_semantic)

        user_prompt = build_user_prompt(
            latest_message=utterance,
            recent_context=recent_ctx,
            semantic_context=semantic_ctx,
        )

        return self.llm.generate(self._system_prompt, user_prompt)

    @staticmethod
    def _schedule(responses: dict[str, str]) -> list[ChatMessage]:
        """
        Assign a random delay to each persona according to DELAY_CONFIG,
        then return messages sorted by ascending delay.
        """
        messages = []
        for persona, text in responses.items():
            lo, hi = DELAY_CONFIG.get(persona, (1.0, 4.0))
            delay = random.uniform(lo, hi)
            messages.append(ChatMessage(persona=persona, text=text, delay=delay, timestamp=0.0))

        messages.sort(key=lambda m: m.delay)
        return messages

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def rag_size(self) -> int:
        return len(self.rag)

    def __repr__(self) -> str:
        return (
            f"RAGLLMPipeline(category={self.stream_category!r}, "
            f"rag_chunks={self.rag_size}, llm={self.llm!r})"
        )
