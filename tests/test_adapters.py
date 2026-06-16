from langchain.schema import Document

from rag_assistant.adapters.chroma import ChromaVectorStoreAdapter


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        lowered = text.lower()
        if "wal" in lowered:
            return [1.0, 0.0]
        if "security" in lowered:
            return [0.0, 1.0]
        return [0.5, 0.5]


def test_chroma_adapter_implements_vector_store_port(tmp_path):
    store = ChromaVectorStoreAdapter(
        db_path=tmp_path / "chroma",
        embeddings=FakeEmbeddings(),
    )
    documents = [
        Document(
            page_content="WAL checkpoint documentation",
            metadata={"chunk_id": "wal-1", "source_type": "docs"},
        ),
        Document(
            page_content="Security configuration",
            metadata={"chunk_id": "security-1", "source_type": "docs"},
        ),
    ]

    store.add_documents(documents, ids=["wal-1", "security-1"])

    assert store.location == str(tmp_path / "chroma")
    assert len(store.list_documents()) == 2
    assert store.similarity_search("WAL failure", k=1)[0].metadata["chunk_id"] == "wal-1"

    store.delete_where({"source_type": "docs"})

    assert store.list_documents() == []
