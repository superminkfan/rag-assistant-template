"""Hybrid retrieval helpers."""

from __future__ import annotations

import math
import re

from rag_assistant.ports import RagDocument, VectorStore


def hybrid_search(
    vector_store: VectorStore,
    query: str,
    *,
    vector_k: int = 6,
    keyword_k: int = 8,
    final_k: int = 6,
) -> list[RagDocument]:
    """Retrieve documents with vector search plus a lightweight keyword pass."""

    vector_docs = vector_store.similarity_search(query, k=vector_k)
    keyword_docs = keyword_search(vector_store, query, k=keyword_k)

    merged: dict[str, tuple[float, RagDocument]] = {}
    for rank, document in enumerate(vector_docs):
        key = document_key(document)
        merged[key] = (merged.get(key, (0.0, document))[0] + 0.25 / (rank + 1), document)

    for rank, document in enumerate(keyword_docs):
        key = document_key(document)
        score = lexical_score(query, getattr(document, "page_content", ""))
        merged[key] = (
            merged.get(key, (0.0, document))[0] + score + 0.5 / (rank + 1),
            document,
        )

    ranked = sorted(merged.values(), key=lambda item: item[0], reverse=True)
    ranked = prefer_strong_incident_matches(query, ranked)
    return [document for _, document in ranked[:final_k]]


def keyword_search(
    vector_store: VectorStore,
    query: str,
    *,
    k: int = 8,
) -> list[RagDocument]:
    """Run a small in-process keyword search over stored documents."""

    if k <= 0:
        return []

    try:
        documents = vector_store.list_documents()
    except Exception:
        return []

    scored: list[tuple[float, RagDocument]] = []
    for document in documents:
        page_content = document.page_content
        if not page_content:
            continue
        score = lexical_score(query, page_content)
        if score <= 0:
            continue
        scored.append((score, document))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [document for _, document in scored[:k]]


def lexical_score(query: str, text: str) -> float:
    """Score exact incident tokens higher than common prose."""

    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0

    text_lower = text.lower()
    text_tokens = tokenize(text)
    if not text_tokens:
        return 0.0

    text_counts: dict[str, int] = {}
    for token in text_tokens:
        text_counts[token] = text_counts.get(token, 0) + 1

    score = 0.0
    for token in query_tokens:
        count = text_counts.get(token, 0)
        if not count:
            continue
        token_weight = token_importance(token)
        score += token_weight * (1.0 + math.log(count))

    normalized_query = " ".join(query_tokens)
    if len(normalized_query) > 12 and normalized_query in text_lower:
        score += 5.0

    return score


def tokenize(text: str) -> list[str]:
    """Tokenize mixed Russian/English technical text."""

    return [
        token.lower()
        for token in re.findall(r"[A-Za-zА-Яа-я0-9_.:/#-]{3,}", text)
        if token.lower() not in STOP_WORDS
    ]


def looks_like_incident_token(token: str) -> bool:
    return (
        "." in token
        or "_" in token
        or "-" in token
        or token.endswith("exception")
        or token.isupper()
        or any(char.isdigit() for char in token)
    )


def token_importance(token: str) -> float:
    """Return a retrieval weight for technical incident tokens."""

    if token in STRONG_INCIDENT_TERMS:
        return 3.0
    if looks_like_incident_token(token):
        return 2.5
    return 0.5


def prefer_strong_incident_matches(
    query: str, ranked: list[tuple[float, RagDocument]]
) -> list[tuple[float, RagDocument]]:
    """Avoid filling technical incident context with one-token generic matches."""

    query_strong_tokens = {
        token for token in tokenize(query) if token in STRONG_INCIDENT_TERMS or looks_like_incident_token(token)
    }
    if len(query_strong_tokens) < 2:
        return ranked

    preferred: list[tuple[float, RagDocument]] = []
    for score, document in ranked:
        document_tokens = set(tokenize(getattr(document, "page_content", "")))
        if len(query_strong_tokens & document_tokens) >= 2:
            preferred.append((score, document))

    return preferred or ranked


def document_key(document: RagDocument) -> str:
    metadata = getattr(document, "metadata", {}) or {}
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    source = metadata.get("source") or metadata.get("source_path") or ""
    return f"{source}:{hash(getattr(document, 'page_content', ''))}"


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "как",
    "для",
    "или",
    "при",
    "что",
    "это",
    "если",
    "чтобы",
    "можно",
    "нужно",
    "need",
    "node",
    "nodes",
    "failed",
    "failure",
    "warning",
    "warnings",
    "symptom",
    "symptoms",
    "diagnostic",
    "diagnostics",
    "mitigation",
}

STRONG_INCIDENT_TERMS = {
    "rmi",
    "tcp",
    "wal",
    "pme",
    "jvm",
    "gc",
    "heap",
    "heapdump",
    "safepoint",
    "checkpoint",
    "checkpointing",
    "commit_memory",
    "os::commit_memory",
    "oom",
    "segmented",
    "deadlock",
    "rebalance",
    "rebalancing",
    "idle_verify",
    "baseline",
}
