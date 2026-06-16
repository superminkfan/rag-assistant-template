"""Chroma vector-store adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import shutil

from rag_assistant.ports import Embeddings, RagDocument


class ChromaVectorStoreAdapter:
    """Hide LangChain Chroma details behind the vector-store port."""

    def __init__(
        self,
        *,
        db_path: Path,
        embeddings: Embeddings,
        reset: bool = False,
    ) -> None:
        from langchain_chroma import Chroma

        if reset and db_path.exists():
            shutil.rmtree(db_path)

        self._db_path = db_path
        self._store = Chroma(
            persist_directory=str(db_path),
            embedding_function=embeddings,
        )

    @property
    def location(self) -> str:
        return str(self._db_path)

    def similarity_search(self, query: str, *, k: int) -> list[RagDocument]:
        return list(self._store.similarity_search(query, k=k))

    def list_documents(self) -> list[RagDocument]:
        from langchain.schema import Document

        raw = self._store.get(include=["documents", "metadatas"])
        documents = raw.get("documents") or []
        metadatas = raw.get("metadatas") or []
        return [
            Document(page_content=page_content, metadata=metadata or {})
            for page_content, metadata in zip(documents, metadatas)
            if page_content
        ]

    def add_documents(
        self,
        documents: Sequence[RagDocument],
        *,
        ids: Sequence[str],
    ) -> None:
        self._store.add_documents(list(documents), ids=list(ids))

    def delete_ids(self, ids: Sequence[str]) -> None:
        self._store.delete(ids=list(ids))

    def delete_where(self, where: Mapping[str, object]) -> None:
        self._store.delete(where=dict(where))
