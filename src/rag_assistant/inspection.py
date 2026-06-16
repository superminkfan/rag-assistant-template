"""Inspect local Chroma indexes without invoking embedding models."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


def inspect_source(
    source_path: Path,
    *,
    source_type: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 180,
    limit: int | None = None,
) -> dict[str, Any]:
    """Dry-run a source loader and chunker without embedding anything."""

    from rag_assistant.docs import load_source_documents
    from rag_assistant.indexing import build_chunks

    documents = load_source_documents(source_path, source_type=source_type)
    if limit is not None:
        documents = documents[:limit]
    chunks, ids = build_chunks(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    metadatas = [chunk.metadata for chunk in chunks]
    return {
        "source_path": str(source_path),
        "source_type": source_type,
        "documents": len(documents),
        "chunks": len(chunks),
        "unique_chunk_ids": len(set(ids)),
        "component": _counter(metadatas, "component"),
        "guide": _counter(metadatas, "guide"),
    }


def format_source_summary(summary: dict[str, Any]) -> str:
    """Format source dry-run data for CLI output."""

    lines = [
        f"Source: {summary['source_path']}",
        f"Source type: {summary['source_type']}",
        f"Documents: {summary['documents']}",
        f"Chunks: {summary['chunks']}",
        f"Unique chunk ids: {summary['unique_chunk_ids']}",
    ]
    _append_counter(lines, "Components", summary.get("component") or {})
    _append_counter(lines, "Guides", summary.get("guide") or {})
    return "\n".join(lines)


def inspect_index(db_path: Path, *, sample_limit: int | None = None) -> dict[str, Any]:
    """Return collection and metadata summaries for a Chroma database."""

    import chromadb

    client = chromadb.PersistentClient(path=str(db_path))
    collections_summary: list[dict[str, Any]] = []

    for collection in client.list_collections():
        count = collection.count()
        limit = count if sample_limit is None else min(count, sample_limit)
        raw = collection.get(include=["metadatas"], limit=limit)
        metadatas = raw.get("metadatas") or []
        collections_summary.append(
            {
                "name": collection.name,
                "count": count,
                "sampled": len(metadatas),
                "source_type": _counter(metadatas, "source_type"),
                "component": _counter(metadatas, "component"),
                "guide": _counter(metadatas, "guide"),
            }
        )

    return {
        "db_path": str(db_path),
        "collections": collections_summary,
    }


def format_index_summary(summary: dict[str, Any]) -> str:
    """Format index inspection data for CLI output."""

    lines = [f"Index: {summary['db_path']}"]
    collections = summary.get("collections") or []
    if not collections:
        lines.append("No collections found.")
        return "\n".join(lines)

    for collection in collections:
        lines.append("")
        lines.append(f"Collection: {collection['name']}")
        lines.append(f"Chunks: {collection['count']}")
        if collection["sampled"] != collection["count"]:
            lines.append(f"Sampled metadata rows: {collection['sampled']}")
        _append_counter(lines, "Source types", collection.get("source_type") or {})
        _append_counter(lines, "Components", collection.get("component") or {})
        _append_counter(lines, "Guides", collection.get("guide") or {})

    return "\n".join(lines)


def _counter(metadatas: list[dict[str, Any]], key: str) -> dict[str, int]:
    values = Counter(str(metadata.get(key) or "unknown") for metadata in metadatas)
    return dict(values.most_common(12))


def _append_counter(lines: list[str], label: str, values: dict[str, int]) -> None:
    if not values:
        return
    formatted = ", ".join(f"{key}={count}" for key, count in values.items())
    lines.append(f"{label}: {formatted}")
