from rag_assistant.docs import SourceDocument
from rag_assistant.indexing import build_chunks, ingest_source, stable_chunk_id


def test_stable_chunk_id_is_position_based():
    first = stable_chunk_id(source_type="datagrid-docs", source_path="a.md", chunk_index=0)
    second = stable_chunk_id(source_type="datagrid-docs", source_path="a.md", chunk_index=0)
    other = stable_chunk_id(source_type="datagrid-docs", source_path="a.md", chunk_index=1)

    assert first == second
    assert first != other


def test_build_chunks_adds_chunk_metadata():
    document = SourceDocument(
        page_content="# Root\n\n" + "Persistence WAL checkpoint. " * 30,
        metadata={
            "source": "documentation/documents/a.md",
            "source_path": "documentation/documents/a.md",
            "source_type": "datagrid-docs",
            "title": "Root",
        },
    )

    chunks, ids = build_chunks([document], chunk_size=120, chunk_overlap=10)

    assert chunks
    assert len(chunks) == len(ids)
    assert chunks[0].metadata["chunk_id"] == ids[0]
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["section"] == "Root"


def test_build_chunks_repeats_context_for_qa_records():
    document = SourceDocument(
        page_content="# WAL problem\n\n## Question\n\n" + "question " * 80 + "\n\n## Response\n\n" + "answer " * 80,
        metadata={
            "source": "https://stackoverflow.com/a/1",
            "source_path": "data/qa.jsonl#stackoverflow:1:response:1",
            "source_type": "stackoverflow-kb",
            "source_format": "qa-pair",
            "record_id": "stackoverflow:1:response:1",
            "record_type": "answered_question",
            "trust_tier": "community",
            "title": "WAL problem",
            "source_url": "https://stackoverflow.com/a/1",
            "is_accepted": True,
        },
    )

    chunks, ids = build_chunks([document], chunk_size=300, chunk_overlap=40)

    assert len(chunks) > 1
    assert len(ids) == len(set(ids))
    assert all("Record ID: stackoverflow:1:response:1" in chunk.page_content for chunk in chunks)
    assert all("Trust Tier: community" in chunk.page_content for chunk in chunks)


def test_ingest_source_uses_injected_vector_store(monkeypatch, tmp_path):
    document = SourceDocument(
        page_content="# Root\n\nPersistence WAL checkpoint.",
        metadata={
            "source": "a.md",
            "source_path": "a.md",
            "source_type": "datagrid-docs",
            "title": "Root",
        },
    )

    class FakeVectorStore:
        location = "memory://test"

        def __init__(self):
            self.deleted_where = []
            self.deleted_ids = []
            self.added = []

        def delete_where(self, where):
            self.deleted_where.append(where)

        def delete_ids(self, ids):
            self.deleted_ids.extend(ids)

        def add_documents(self, documents, *, ids):
            self.added.append((list(documents), list(ids)))

    store = FakeVectorStore()
    monkeypatch.setattr(
        "rag_assistant.indexing.load_source_documents",
        lambda source_path, source_type: [document],
    )

    stats = ingest_source(
        tmp_path,
        vector_store=store,
        source_type="datagrid-docs",
        batch_size=1,
        replace_source_type=True,
    )

    assert stats["documents"] == 1
    assert stats["chunks"] == 1
    assert stats["db_path"] == "memory://test"
    assert store.deleted_where == [{"source_type": "datagrid-docs"}]
    assert len(store.deleted_ids) == 1
    assert len(store.added) == 1
    assert store.added[0][1] == store.deleted_ids


def test_ingest_source_can_replace_only_one_source_id(monkeypatch, tmp_path):
    document = SourceDocument(
        page_content="# Page\n\nConfluence technical content.",
        metadata={
            "source": "https://wiki.example/page/1",
            "source_path": "https://wiki.example/page/1",
            "source_type": "confluence-snapshot",
            "source_id": "sberworks",
            "title": "Page",
        },
    )

    class FakeVectorStore:
        location = "memory://test"

        def __init__(self):
            self.deleted_where = []

        def delete_where(self, where):
            self.deleted_where.append(where)

        def delete_ids(self, ids):
            pass

        def add_documents(self, documents, *, ids):
            pass

    store = FakeVectorStore()
    monkeypatch.setattr(
        "rag_assistant.indexing.load_source_documents",
        lambda source_path, source_type: [document],
    )

    ingest_source(
        tmp_path,
        vector_store=store,
        source_type="confluence-snapshot",
        replace_source_id=True,
    )

    assert store.deleted_where == [{"source_id": "sberworks"}]
