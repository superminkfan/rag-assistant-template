"""Hybrid retrieval helpers."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re

from rag_assistant.ports import RagDocument, VectorStore


def hybrid_search(
    vector_store: VectorStore,
    query: str,
    *,
    vector_k: int = 24,
    keyword_k: int = 32,
    final_k: int = 6,
) -> list[RagDocument]:
    """Retrieve a broad candidate pool, then rerank to a compact context."""

    candidates = collect_candidates(
        vector_store,
        query,
        vector_k=vector_k,
        keyword_k=keyword_k,
    )
    ranked = rerank_candidates(query, candidates)
    ranked = prefer_strong_incident_matches(query, ranked)
    return select_final_context(ranked, final_k)


@dataclass
class RetrievalCandidate:
    """A merged retrieval candidate with source-specific ranks."""

    document: RagDocument
    vector_rank: int | None = None
    keyword_rank: int | None = None
    keyword_score: float = 0.0


def collect_candidates(
    vector_store: VectorStore,
    query: str,
    *,
    vector_k: int,
    keyword_k: int,
) -> list[RetrievalCandidate]:
    """Collect candidates from semantic and lexical retrieval passes."""

    vector_docs = (
        vector_store.similarity_search(query, k=vector_k)
        if vector_k > 0
        else []
    )
    keyword_docs = keyword_search(vector_store, query, k=keyword_k)
    return merge_candidates(query, vector_docs=vector_docs, keyword_docs=keyword_docs)


def merge_candidates(
    query: str,
    *,
    vector_docs: list[RagDocument],
    keyword_docs: list[RagDocument],
) -> list[RetrievalCandidate]:
    """Deduplicate vector and keyword candidates while keeping rank signals."""

    candidates: dict[str, RetrievalCandidate] = {}

    for rank, document in enumerate(vector_docs):
        key = document_key(document)
        candidate = candidates.setdefault(key, RetrievalCandidate(document=document))
        if candidate.vector_rank is None or rank < candidate.vector_rank:
            candidate.vector_rank = rank

    for rank, document in enumerate(keyword_docs):
        key = document_key(document)
        candidate = candidates.setdefault(key, RetrievalCandidate(document=document))
        if candidate.keyword_rank is None or rank < candidate.keyword_rank:
            candidate.keyword_rank = rank
        candidate.keyword_score = max(
            candidate.keyword_score,
            lexical_score(query, getattr(document, "page_content", "")),
        )

    return list(candidates.values())


def rerank_candidates(
    query: str,
    candidates: list[RetrievalCandidate],
) -> list[tuple[float, RagDocument]]:
    """Rank merged candidates using deterministic text, rank, and metadata signals."""

    ranked = [
        (candidate_score(query, candidate), candidate.document)
        for candidate in candidates
    ]
    return sorted(ranked, key=lambda item: item[0], reverse=True)


def candidate_score(query: str, candidate: RetrievalCandidate) -> float:
    """Compute a deterministic relevance score for a merged candidate."""

    document = candidate.document
    score = 0.0

    if candidate.vector_rank is not None:
        score += 1.0 / (candidate.vector_rank + 1)
    if candidate.keyword_rank is not None:
        score += 1.5 / (candidate.keyword_rank + 1)

    score += candidate.keyword_score
    score += metadata_score(query, document)
    score += strong_token_coverage_boost(query, document)
    return score


def select_final_context(
    ranked: list[tuple[float, RagDocument]],
    final_k: int,
) -> list[RagDocument]:
    """Return only the compact set that should be inserted into the prompt."""

    if final_k <= 0:
        return []
    return [document for _, document in ranked[:final_k]]


def keyword_search(
    vector_store: VectorStore,
    query: str,
    *,
    k: int = 32,
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


def metadata_score(query: str, document: RagDocument) -> float:
    """Score query-token matches in metadata that helps source selection."""

    metadata = getattr(document, "metadata", {}) or {}
    score = 0.0
    score += _metadata_field_score(query, metadata.get("title"), weight=1.5)
    score += _metadata_field_score(query, metadata.get("section"), weight=1.0)
    score += _metadata_field_score(query, metadata.get("component"), weight=0.8)
    source = metadata.get("source_path") or metadata.get("source")
    score += _metadata_field_score(query, source, weight=0.3)
    return score


def strong_token_coverage_boost(query: str, document: RagDocument) -> float:
    """Reward candidates that cover several exact incident tokens."""

    query_strong_tokens = {
        token
        for token in tokenize(query)
        if token in STRONG_INCIDENT_TERMS or looks_like_incident_token(token)
    }
    if len(query_strong_tokens) < 2:
        return 0.0

    document_tokens = _document_tokens(document)
    overlap_count = len(query_strong_tokens & document_tokens)
    if overlap_count < 2:
        return 0.0
    return (overlap_count * 1.5) + (overlap_count / len(query_strong_tokens) * 2.0)


def _metadata_field_score(query: str, value: object, *, weight: float) -> float:
    if not value:
        return 0.0

    query_tokens = set(tokenize(query))
    field_tokens = set(tokenize(str(value)))
    if not query_tokens or not field_tokens:
        return 0.0

    score = 0.0
    for token in query_tokens & field_tokens:
        score += token_importance(token) * weight
    return score


def _document_tokens(document: RagDocument) -> set[str]:
    metadata = getattr(document, "metadata", {}) or {}
    metadata_text = " ".join(
        str(metadata.get(key) or "")
        for key in ("title", "section", "component", "source_path", "source")
    )
    return set(tokenize(f"{getattr(document, 'page_content', '')}\n{metadata_text}"))


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
        document_tokens = _document_tokens(document)
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
