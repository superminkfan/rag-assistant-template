"""Application ports for model, embedding, storage, and retrieval adapters."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class RagDocument(Protocol):
    """Minimal document shape used by the application layer."""

    page_content: str
    metadata: dict[str, Any]


class LLM(Protocol):
    """Text generation port."""

    def generate(self, prompt: str) -> str:
        """Generate text for a prompt."""


class Embeddings(Protocol):
    """Embedding model port compatible with vector-store adapters."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a retrieval query."""


class VectorStore(Protocol):
    """Vector storage operations required by indexing and retrieval."""

    @property
    def location(self) -> str:
        """Return a human-readable storage location."""

    def similarity_search(self, query: str, *, k: int) -> list[RagDocument]:
        """Return documents nearest to the query embedding."""

    def list_documents(self) -> list[RagDocument]:
        """Return documents for the local lexical retrieval pass."""

    def add_documents(
        self,
        documents: Sequence[RagDocument],
        *,
        ids: Sequence[str],
    ) -> None:
        """Store documents under stable ids."""

    def delete_ids(self, ids: Sequence[str]) -> None:
        """Delete documents by id."""

    def delete_where(self, where: Mapping[str, object]) -> None:
        """Delete documents matching metadata."""


class Retriever(Protocol):
    """Context retrieval port used by RAG scenarios."""

    def retrieve(self, query: str, *, limit: int | None = None) -> list[RagDocument]:
        """Retrieve context for a user query."""
