"""Build vector-store chunks from normalized documentation."""

from __future__ import annotations

from pathlib import Path
import hashlib
from collections.abc import Callable

from rag_assistant.docs import SourceDocument, iter_source_sections, load_source_documents
from rag_assistant.ports import VectorStore


def build_chunks(
    documents: list[SourceDocument],
    *,
    chunk_size: int = 1200,
    chunk_overlap: int = 180,
) -> tuple[list[object], list[str]]:
    """Split source documents into LangChain Documents with stable ids."""

    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    sections: list[Document] = []
    jira_chunks: list[Document] = []
    for document in documents:
        if document.metadata.get("source_format") == "jira-snapshot":
            jira_chunks.extend(
                _split_jira_snapshot_document(
                    document,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            )
            continue
        for section in iter_source_sections(document):
            sections.append(
                Document(page_content=section.page_content, metadata=section.metadata)
            )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=[
            "\n# ",
            "\n## ",
            "\n### ",
            "\n#### ",
            "\n= ",
            "\n== ",
            "\n=== ",
            "\n==== ",
            "\n```",
            "\n----\n",
            "\n....\n",
            "\n\n",
            "\n- ",
            "\n* ",
            "\n",
            " ",
            "",
        ],
        keep_separator=False,
        strip_whitespace=False,
    )
    chunks = splitter.split_documents(sections) + jira_chunks

    ids: list[str] = []
    source_counts: dict[str, int] = {}
    for chunk in chunks:
        source = str(chunk.metadata.get("source_path") or chunk.metadata.get("source") or "")
        source_counts[source] = source_counts.get(source, 0) + 1
        chunk_index = source_counts[source] - 1
        chunk_id = stable_chunk_id(
            source_type=str(chunk.metadata.get("source_type") or ""),
            source_path=source,
            chunk_index=chunk_index,
        )
        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["chunk_id"] = chunk_id
        ids.append(chunk_id)

    return chunks, ids


def _split_jira_snapshot_document(
    document: SourceDocument,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[object]:
    """Split Jira record text while repeating record context in every chunk."""

    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    prefix = _jira_chunk_prefix(document.metadata)
    body_chunk_size = max(80, chunk_size - len(prefix) - 2)
    body_overlap = min(chunk_overlap, max(0, body_chunk_size // 4))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=body_chunk_size,
        chunk_overlap=body_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
        keep_separator=False,
    )
    parts = splitter.split_text(document.page_content) or [document.page_content]
    return [
        Document(
            page_content=f"{prefix}\n\n{part.strip()}\n",
            metadata=dict(document.metadata),
        )
        for part in parts
        if part.strip()
    ]


def _jira_chunk_prefix(metadata: dict[str, object]) -> str:
    lines = [
        f"Issue Key: {metadata.get('issue_key') or 'unknown'}",
        f"Support Key: {metadata.get('support_key') or 'unknown'}",
        f"Title: {metadata.get('title') or 'unknown'}",
        f"Record Type: {metadata.get('record_type') or 'unknown'}",
    ]
    if metadata.get("record_type") == "comment":
        lines.extend(
            [
                f"Comment ID: {metadata.get('comment_id') or 'unknown'}",
                f"Author: {metadata.get('author') or 'unknown'}",
                f"Created: {metadata.get('comment_created_at') or 'unknown'}",
            ]
        )
    return "\n".join(lines)


def ingest_source(
    source_path: Path,
    *,
    vector_store: VectorStore,
    source_type: str = "datagrid-docs",
    chunk_size: int = 1200,
    chunk_overlap: int = 180,
    limit: int | None = None,
    batch_size: int = 64,
    replace_source_type: bool = False,
    progress: Callable[[str], None] | None = None,
) -> dict[str, int | str]:
    """Ingest documentation through the configured vector-store port."""

    source_documents = load_source_documents(source_path, source_type=source_type)
    if limit is not None:
        source_documents = source_documents[:limit]
    if progress:
        progress(f"Loaded {len(source_documents)} source documents.")

    chunks, ids = build_chunks(
        source_documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if progress:
        progress(f"Split source documents into {len(chunks)} chunks.")

    if replace_source_type:
        vector_store.delete_where({"source_type": source_type})
        if progress:
            progress(f"Deleted existing chunks with source_type={source_type}.")

    for start in range(0, len(chunks), batch_size):
        end = min(start + batch_size, len(chunks))
        try:
            vector_store.delete_ids(ids[start:end])
        except Exception:
            pass
        vector_store.add_documents(chunks[start:end], ids=ids[start:end])
        if progress:
            progress(f"Embedded {end}/{len(chunks)} chunks.")

    return {
        "documents": len(source_documents),
        "chunks": len(chunks),
        "db_path": vector_store.location,
    }


def stable_chunk_id(*, source_type: str, source_path: str, chunk_index: int) -> str:
    """Return a stable Chroma id for a source chunk position."""

    raw = f"{source_type}:{source_path}:{chunk_index}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()
