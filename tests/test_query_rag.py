import sys
import types
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
    monkeypatch.setenv(ollama.SIMILARITY_K_ENV_VAR, "4")

    response = ollama.query_rag(ChatMessage(question="Hello"), session_id="thread-1")

    assert ensure_calls["count"] == 1
    assert response == "answer:Hello"
    assert db.queries == [("Hello", 4)]

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
    monkeypatch.setenv(ollama.SIMILARITY_K_ENV_VAR, "2")

    response = ollama.query_rag(ChatMessage(question="Follow up"), session_id="thread-2")

    assert ensure_calls["count"] == 1
    assert response == "answer:Follow up"
    assert db.queries == [("Follow up", 2)]

    assert chain.calls[0]["chat_history"] is existing_history
    assert existing_history[-2].content == "Follow up"
    assert existing_history[-1].content == "answer:Follow up"
    assert len(existing_history) == 4


def test_prompt_template_includes_guidance(monkeypatch):
    captured = {}

    class DummyPromptTemplate:
        @classmethod
        def from_messages(cls, messages):
            captured["messages"] = messages
            return "prompt"

    class DummyMessagesPlaceholder:
        def __init__(self, variable_name):
            self.variable_name = variable_name

    class DummyMessage:
        def __init__(self, content=""):
            self.content = content

    class DummyLLM:
        def __init__(self, *_, **__):
            pass

    class DummyEmbeddings(DummyLLM):
        pass

    class DummyChroma:
        def __init__(self, *_, **__):
            pass

    def fake_create_chain(*_, **kwargs):
        captured["chain_kwargs"] = kwargs
        return "chain"

    prompts_module = types.ModuleType("langchain_core.prompts")
    setattr(prompts_module, "ChatPromptTemplate", DummyPromptTemplate)
    setattr(prompts_module, "MessagesPlaceholder", DummyMessagesPlaceholder)

    messages_module = types.ModuleType("langchain_core.messages")
    setattr(messages_module, "AIMessage", DummyMessage)
    setattr(messages_module, "HumanMessage", DummyMessage)

    ollama_module = types.ModuleType("langchain_ollama")
    setattr(ollama_module, "OllamaLLM", DummyLLM)
    setattr(ollama_module, "OllamaEmbeddings", DummyEmbeddings)

    chroma_module = types.ModuleType("langchain_chroma")
    setattr(chroma_module, "Chroma", DummyChroma)

    chains_module = types.ModuleType("langchain.chains.combine_documents")
    setattr(chains_module, "create_stuff_documents_chain", fake_create_chain)

    monkeypatch.setitem(sys.modules, "langchain_core.prompts", prompts_module)
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages_module)
    monkeypatch.setitem(sys.modules, "langchain_ollama", ollama_module)
    monkeypatch.setitem(sys.modules, "langchain_chroma", chroma_module)
    monkeypatch.setitem(sys.modules, "langchain.chains.combine_documents", chains_module)

    monkeypatch.setattr(ollama, "_document_chain", None)
    monkeypatch.setattr(ollama, "_db", None)
    monkeypatch.setattr(ollama, "_human_message_cls", None)
    monkeypatch.setattr(ollama, "_ai_message_cls", None)

    ollama._ensure_initialized()

    system_message = captured["messages"][0][1]
    assert "numbered citations" in system_message
    assert "ordered list" in system_message or "sequence of steps" in system_message
