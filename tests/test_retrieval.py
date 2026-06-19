from rag_assistant.adapters.retrieval import HybridRetriever
from rag_assistant.retrieval import (
    RetrievalCandidate,
    hybrid_search,
    merge_candidates,
    rerank_candidates,
    lexical_score,
    prefer_strong_incident_matches,
    tokenize,
)
from rag_assistant.rag import (
    append_sources,
    build_incident_prompt,
    ensure_incident_section_citations,
    normalize_incident_report_headings,
)


class Doc:
    def __init__(self, text, metadata=None):
        self.page_content = text
        self.metadata = metadata or {}


def test_tokenize_keeps_incident_terms():
    tokens = tokenize("Failed to wait for partition map exchange and WAL archive")

    assert "partition" in tokens
    assert "wal" in tokens
    assert "archive" in tokens
    assert "for" not in tokens


def test_lexical_score_rewards_exact_incident_terms():
    query = "Failed to wait for partition map exchange"
    matching = "WARN Failed to wait for partition map exchange topVer=AffinityTopologyVersion"
    unrelated = "Настройка безопасности и сертификатов"

    assert lexical_score(query, matching) > lexical_score(query, unrelated)


def test_lexical_score_downranks_generic_node_overlap():
    query = "DataGrid node failed OpenJDK os::commit_memory warning TCP RMI threads"
    incident_match = "OpenJDK os::commit_memory failed because many RMI TCP threads were created"
    generic_match = "JDBC client node can connect over TCP"

    assert lexical_score(query, incident_match) > lexical_score(query, generic_match) * 2


def test_prefer_strong_incident_matches_removes_one_token_noise():
    ranked = [
        (3.0, Doc("OpenJDK os::commit_memory failed with RMI TCP threads")),
        (2.0, Doc("JDBC node connects over TCP")),
    ]

    filtered = prefer_strong_incident_matches(
        "OpenJDK os::commit_memory TCP RMI threads",
        ranked,
    )

    assert len(filtered) == 1
    assert "os::commit_memory" in filtered[0][1].page_content


def test_merge_candidates_deduplicates_by_chunk_id_and_keeps_ranks():
    document = Doc(
        "WAL checkpoint documentation",
        {"chunk_id": "wal-1"},
    )

    candidates = merge_candidates(
        "WAL checkpoint",
        vector_docs=[document],
        keyword_docs=[document],
    )

    assert len(candidates) == 1
    assert candidates[0].vector_rank == 0
    assert candidates[0].keyword_rank == 0
    assert candidates[0].keyword_score > 0


def test_rerank_candidates_uses_metadata_matches():
    metadata_match = Doc(
        "General persistence documentation",
        {"chunk_id": "a", "title": "WAL checkpointing"},
    )
    text_only = Doc(
        "General persistence documentation",
        {"chunk_id": "b", "title": "Security"},
    )

    ranked = rerank_candidates(
        "WAL checkpointing",
        [
            RetrievalCandidate(document=text_only),
            RetrievalCandidate(document=metadata_match),
        ],
    )

    assert ranked[0][1] is metadata_match


def test_hybrid_search_uses_broad_candidate_pool_and_final_k():
    class Store:
        def __init__(self):
            self.vector_k = None

        def similarity_search(self, query, *, k):
            self.vector_k = k
            return [
                Doc("Generic persistence guide", {"chunk_id": "generic"}),
                Doc("WAL checkpoint documentation", {"chunk_id": "wal"}),
            ]

        def list_documents(self):
            return [
                Doc("WAL checkpoint documentation", {"chunk_id": "wal"}),
                Doc("Security configuration", {"chunk_id": "security"}),
            ]

    store = Store()

    result = hybrid_search(
        store,
        "WAL checkpoint",
        vector_k=24,
        keyword_k=32,
        final_k=1,
    )

    assert store.vector_k == 24
    assert len(result) == 1
    assert result[0].metadata["chunk_id"] == "wal"


def test_hybrid_retriever_limit_controls_final_context_only():
    class Store:
        def similarity_search(self, query, *, k):
            return [
                Doc("WAL checkpoint documentation", {"chunk_id": "wal"}),
                Doc("Security configuration", {"chunk_id": "security"}),
            ]

        def list_documents(self):
            return [
                Doc("WAL checkpoint documentation", {"chunk_id": "wal"}),
                Doc("Security configuration", {"chunk_id": "security"}),
            ]

    retriever = HybridRetriever(Store(), vector_k=24, keyword_k=32, final_k=6)

    result = retriever.retrieve("WAL checkpoint", limit=1)

    assert len(result) == 1
    assert result[0].metadata["chunk_id"] == "wal"


def test_append_sources_groups_same_source():
    class Doc:
        def __init__(self, source_id):
            self.metadata = {
                "source_id": source_id,
                "source": "docs/a.md",
                "title": "A",
            }

    response = append_sources("answer", [Doc("1"), Doc("2")])

    assert response.endswith("Sources:\n[1], [2] docs/a.md - A")


def test_incident_prompt_requires_section_citations():
    class Doc:
        page_content = "Evidence text"
        metadata = {"source_id": "1", "source": "docs/a.md", "title": "A"}

    prompt = build_incident_prompt("incident", [Doc()])

    assert "Каждый пункт в Evidence, Diagnostics и Mitigation" in prompt
    assert "гипотеза" in prompt


def test_ensure_incident_section_citations_adds_fallback_to_bullets():
    class Doc:
        metadata = {"source_id": "3"}

    response = """Summary
No citation here.

Evidence
- Missing citation
- Already cited [2]

Diagnostics
1. Check logs
"""

    updated = ensure_incident_section_citations(response, [Doc()])

    assert "- Missing citation [3]" in updated
    assert "- Already cited [2]" in updated
    assert "1. Check logs [3]" in updated
    assert "No citation here. [3]" not in updated


def test_normalize_incident_report_headings_fixes_heading_drift():
    response = """Сумmarу
----------
Text

Likely Cause
-------------
Cause
"""

    normalized = normalize_incident_report_headings(response)

    assert normalized.startswith("Summary\nText")
    assert "----------" not in normalized
    assert "Likely Cause\nCause" in normalized
