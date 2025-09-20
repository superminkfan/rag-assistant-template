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


def _install_llm_dependencies(monkeypatch, temperature_capture):
    module = types.ModuleType("langchain_ollama")

    class DummyLLM:
        def __init__(self, model: str, temperature: float):
            temperature_capture.append((model, temperature))

    class DummyEmbeddings:
        def __init__(self, model: str):
            self.model = model

    module.OllamaLLM = DummyLLM
    module.OllamaEmbeddings = DummyEmbeddings
    monkeypatch.setitem(sys.modules, "langchain_ollama", module)

    chroma_module = types.ModuleType("langchain_chroma")

    class DummyChroma:
        def __init__(self, persist_directory, embedding_function):
            self.persist_directory = persist_directory
            self.embedding_function = embedding_function

        def similarity_search(self, *_args, **_kwargs):
            return []

    chroma_module.Chroma = DummyChroma
    monkeypatch.setitem(sys.modules, "langchain_chroma", chroma_module)

    messages_module = types.ModuleType("langchain_core.messages")

    class DummyHumanMessage:
        def __init__(self, content: str):
            self.content = content

    class DummyAIMessage(DummyHumanMessage):
        pass

    messages_module.HumanMessage = DummyHumanMessage
    messages_module.AIMessage = DummyAIMessage
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages_module)

    prompts_module = types.ModuleType("langchain_core.prompts")

    class DummyPromptTemplate:
        def __init__(self, messages):
            self.messages = messages

        @classmethod
        def from_messages(cls, messages):
            return cls(messages)

    class DummyMessagesPlaceholder:
        def __init__(self, variable_name: str):
            self.variable_name = variable_name

    prompts_module.ChatPromptTemplate = DummyPromptTemplate
    prompts_module.MessagesPlaceholder = DummyMessagesPlaceholder
    monkeypatch.setitem(sys.modules, "langchain_core.prompts", prompts_module)

    chains_module = types.ModuleType("langchain.chains.combine_documents")

    class DummyChain:
        def __init__(self, llm, prompt):
            self.llm = llm
            self.prompt = prompt

        def invoke(self, *_args, **_kwargs):
            return ""

    def factory(llm, prompt):
        return DummyChain(llm=llm, prompt=prompt)

    chains_module.create_stuff_documents_chain = factory
    monkeypatch.setitem(sys.modules, "langchain.chains.combine_documents", chains_module)


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


def test_ensure_initialized_uses_configured_temperature(monkeypatch):
    captured_temps = []
    _install_llm_dependencies(monkeypatch, captured_temps)

    monkeypatch.setattr(ollama, "_db", None)
    monkeypatch.setattr(ollama, "_document_chain", None)
    monkeypatch.setattr(ollama, "_human_message_cls", None)
    monkeypatch.setattr(ollama, "_ai_message_cls", None)

    monkeypatch.delenv(ollama.OLLAMA_TEMPERATURE_ENV, raising=False)
    ollama._ensure_initialized()
    assert captured_temps[-1][1] == ollama.DEFAULT_TEMPERATURE

    monkeypatch.setattr(ollama, "_db", None)
    monkeypatch.setattr(ollama, "_document_chain", None)
    monkeypatch.setattr(ollama, "_human_message_cls", None)
    monkeypatch.setattr(ollama, "_ai_message_cls", None)

    captured_temps.clear()
    monkeypatch.setenv(ollama.OLLAMA_TEMPERATURE_ENV, "0.42")
    ollama._ensure_initialized()
    assert captured_temps[-1] == ("llama3.2:latest", 0.42)
