"""Retriever adapters composed from vector-store operations."""

from __future__ import annotations

from rag_assistant.ports import RagDocument, VectorStore
from rag_assistant.retrieval import hybrid_search


class HybridRetriever:
    """Combine dense vector retrieval with the local lexical pass."""

    def __init__(
        self,
        vector_store: VectorStore,
        *,
        vector_k: int,
        keyword_k: int,
        final_k: int,
    ) -> None:
        self._vector_store = vector_store
        self._vector_k = vector_k
        self._keyword_k = keyword_k
        self._final_k = final_k

    def retrieve(self, query: str, *, limit: int | None = None) -> list[RagDocument]:
        return hybrid_search(
            self._vector_store,
            query,
            vector_k=self._vector_k,
            keyword_k=self._keyword_k,
            final_k=self._final_k if limit is None else limit,
        )
