from dataclasses import dataclass, field

from rag_assistant.rag import analyze_incident, ask


@dataclass
class FakeDocument:
    page_content: str
    metadata: dict[str, str] = field(default_factory=dict)


class FakeLLM:
    def __init__(self, response: str):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FakeRetriever:
    def __init__(self, documents):
        self.documents = documents
        self.queries = []

    def retrieve(self, query: str, *, limit=None):
        self.queries.append((query, limit))
        return self.documents


def test_ask_uses_injected_llm_and_retriever():
    llm = FakeLLM("Use WAL settings [1].")
    retriever = FakeRetriever(
        [
            FakeDocument(
                "WAL documentation",
                {"source": "persistence/wal.md", "title": "WAL"},
            )
        ]
    )

    response = ask("How should WAL be configured?", llm=llm, retriever=retriever)

    assert retriever.queries == [("How should WAL be configured?", None)]
    assert "How should WAL be configured?" in llm.prompts[0]
    assert "WAL documentation" in llm.prompts[0]
    assert response.endswith("Sources:\n[1] persistence/wal.md - WAL")


def test_ask_does_not_call_llm_without_context():
    llm = FakeLLM("must not be used")
    retriever = FakeRetriever([])

    response = ask("unknown", llm=llm, retriever=retriever)

    assert response == "Не нашел релевантных источников в локальной базе."
    assert llm.prompts == []


def test_analyze_incident_uses_injected_dependencies():
    llm = FakeLLM("Summary\nIssue\n\nEvidence\n- Check WAL")
    retriever = FakeRetriever(
        [FakeDocument("WAL evidence", {"source": "wal.md", "title": "WAL"})]
    )

    response = analyze_incident(
        "WAL archive grows quickly",
        llm=llm,
        retriever=retriever,
    )

    assert retriever.queries == [("WAL archive grows quickly", None)]
    assert "- Check WAL [1]" in response
    assert response.endswith("Sources:\n[1] wal.md - WAL")
