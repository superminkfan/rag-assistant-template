"""Chroma vector-store adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
import json
from pathlib import Path
import re
import shutil
import sqlite3
from typing import Iterator

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
        self._lexical_path = db_path / "rag_lexical.sqlite3"
        self._store = Chroma(
            persist_directory=str(db_path),
            embedding_function=embeddings,
        )
        self._ensure_lexical_index()

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

    def keyword_search(self, query: str, *, k: int) -> list[RagDocument]:
        """Search the persistent local FTS5 sidecar using BM25 ranking."""

        from langchain.schema import Document

        if k <= 0:
            return []
        tokens = list(
            dict.fromkeys(
                token.lower()
                for token in re.findall(r"[A-Za-zА-Яа-я0-9_]{2,}", query)
            )
        )
        if not tokens:
            return []
        self._ensure_lexical_index()
        match_query = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens)
        with self._lexical_connection() as connection:
            rows = connection.execute(
                """
                SELECT content, metadata_json
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY bm25(documents_fts)
                LIMIT ?
                """,
                (match_query, k),
            ).fetchall()
        return [
            Document(page_content=content, metadata=json.loads(metadata_json))
            for content, metadata_json in rows
        ]

    def add_documents(
        self,
        documents: Sequence[RagDocument],
        *,
        ids: Sequence[str],
    ) -> None:
        stored_documents = list(documents)
        stored_ids = list(ids)
        self._store.add_documents(stored_documents, ids=stored_ids)
        self._upsert_lexical(stored_documents, stored_ids)

    def delete_ids(self, ids: Sequence[str]) -> None:
        stored_ids = list(ids)
        self._store.delete(ids=stored_ids)
        self._delete_lexical_ids(stored_ids)

    def delete_where(self, where: Mapping[str, object]) -> None:
        matched_ids: list[str] = []
        try:
            raw = self._store.get(where=dict(where), include=["metadatas"])
            matched_ids = list(raw.get("ids") or [])
        except Exception:
            pass
        self._store.delete(where=dict(where))
        if matched_ids:
            self._delete_lexical_ids(matched_ids)

    def rebuild_lexical_index(self) -> int:
        """Rebuild the FTS5 sidecar from all documents currently stored in Chroma."""

        raw = self._store.get(include=["documents", "metadatas"])
        ids = list(raw.get("ids") or [])
        documents = list(raw.get("documents") or [])
        metadatas = list(raw.get("metadatas") or [])
        with self._lexical_connection() as connection:
            connection.execute("DELETE FROM documents_fts")
            connection.executemany(
                "INSERT INTO documents_fts(doc_id, content, metadata_json) VALUES (?, ?, ?)",
                [
                    (
                        str(doc_id),
                        str(content or ""),
                        json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
                    )
                    for doc_id, content, metadata in zip(ids, documents, metadatas)
                    if content
                ],
            )
        return len(ids)

    def _ensure_lexical_index(self) -> None:
        with self._lexical_connection() as connection:
            lexical_count = int(
                connection.execute("SELECT count(*) FROM documents_fts").fetchone()[0]
            )
        chroma_count = int(self._store._collection.count())
        if lexical_count != chroma_count:
            self.rebuild_lexical_index()

    def _upsert_lexical(
        self,
        documents: Sequence[RagDocument],
        ids: Sequence[str],
    ) -> None:
        if not ids:
            return
        with self._lexical_connection() as connection:
            connection.executemany(
                "DELETE FROM documents_fts WHERE doc_id = ?",
                [(str(doc_id),) for doc_id in ids],
            )
            connection.executemany(
                "INSERT INTO documents_fts(doc_id, content, metadata_json) VALUES (?, ?, ?)",
                [
                    (
                        str(doc_id),
                        str(document.page_content),
                        json.dumps(document.metadata or {}, ensure_ascii=False, sort_keys=True),
                    )
                    for doc_id, document in zip(ids, documents)
                ],
            )

    def _delete_lexical_ids(self, ids: Sequence[str]) -> None:
        if not ids:
            return
        with self._lexical_connection() as connection:
            connection.executemany(
                "DELETE FROM documents_fts WHERE doc_id = ?",
                [(str(doc_id),) for doc_id in ids],
            )

    @contextmanager
    def _lexical_connection(self) -> Iterator[sqlite3.Connection]:
        self._db_path.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._lexical_path)
        try:
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    doc_id UNINDEXED,
                    content,
                    metadata_json UNINDEXED,
                    tokenize = 'unicode61 remove_diacritics 2'
                )
                """
            )
            yield connection
            connection.commit()
        finally:
            connection.close()
