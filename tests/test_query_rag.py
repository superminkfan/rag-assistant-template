import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.index import ChatMessage
from providers import ollama


class DummyHuman:
    def __init__(self, content: str):
        self.content = content


class DummyAI(DummyHuman):
    pass


class DummyDB:
    def __init__(self):
        self.queries = []

    def similarity_search(self, question: str, k: int):
        self.queries.append((question, k))
        return [f"doc:{question}"]


class DummyChain:
    def __init__(self):
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return f"answer:{payload['question']}"


def _configure_stubbed_rag(monkeypatch):
    db = DummyDB()
    chain = DummyChain()
    ensure_calls = {"count": 0}

    def fake_ensure():
        ensure_calls["count"] += 1
        ollama._db = db
        ollama._document_chain = chain
        ollama._human_message_cls = DummyHuman
        ollama._ai_message_cls = DummyAI

    monkeypatch.setattr(ollama, "_ensure_initialized", fake_ensure)
    monkeypatch.setattr(ollama, "_db", None)
    monkeypatch.setattr(ollama, "_document_chain", None)
    monkeypatch.setattr(ollama, "_human_message_cls", None)
    monkeypatch.setattr(ollama, "_ai_message_cls", None)

    return ensure_calls, db, chain


def test_query_rag_initializes_and_records_history(monkeypatch):
    ensure_calls, db, chain = _configure_stubbed_rag(monkeypatch)
    monkeypatch.setattr(ollama, "chat_history", {})

    response = ollama.query_rag(ChatMessage(question="Hello"), session_id="thread-1")

    assert ensure_calls["count"] == 1
    assert response == "answer:Hello"
    assert db.queries == [("Hello", 3)]

    history = ollama.chat_history["thread-1"]
    assert chain.calls[0]["chat_history"] is history
    assert len(history) == 2
    assert isinstance(history[0], DummyHuman)
    assert history[0].content == "Hello"
    assert isinstance(history[1], DummyAI)
    assert history[1].content == "answer:Hello"


def test_query_rag_reuses_existing_history(monkeypatch):
    ensure_calls, db, chain = _configure_stubbed_rag(monkeypatch)
    existing_history = [DummyHuman("prev question"), DummyAI("prev answer")]
    monkeypatch.setattr(ollama, "chat_history", {"thread-2": existing_history})

    response = ollama.query_rag(ChatMessage(question="Follow up"), session_id="thread-2")

    assert ensure_calls["count"] == 1
    assert response == "answer:Follow up"
    assert db.queries == [("Follow up", 3)]

    assert chain.calls[0]["chat_history"] is existing_history
    assert existing_history[-2].content == "Follow up"
    assert existing_history[-1].content == "answer:Follow up"
    assert len(existing_history) == 4
