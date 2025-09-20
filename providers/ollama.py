import os
from typing import Dict, List

from models.index import ChatMessage


CHROMA_PATH = "./db_metadata_v5"
OLLAMA_TEMPERATURE_ENV = "OLLAMA_TEMPERATURE"
DEFAULT_TEMPERATURE = 0.1

_db = None
_document_chain = None
_human_message_cls = None
_ai_message_cls = None
chat_history: Dict[str, List[object]] = {}


def _ensure_initialized() -> None:
    """Lazily initialize heavy RAG dependencies."""

    global _db, _document_chain, _human_message_cls, _ai_message_cls

    if _document_chain is not None:
        return

    from langchain_chroma import Chroma
    from langchain_core.messages import AIMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_ollama import OllamaEmbeddings, OllamaLLM
    from langchain.chains.combine_documents import create_stuff_documents_chain

    temperature = _get_configured_temperature()
    model = OllamaLLM(model="llama3.2:latest", temperature=temperature)
    embedding_function = OllamaEmbeddings(model="mxbai-embed-large")

    _db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                [INST]You are an IT support specialist. Provide clear, professional, and efficient assistance based solely on the supplied context.
                If the answer is not included in the context, reply exactly “Hmm, I am not sure. Let me check and get back to you.”
                Decline to answer questions that fall outside the provided information.
                Ask for clarification whenever a request is unclear.
                Keep responses concise, objective, and formatted in Markdown when helpful.[/INST]
                [INST]Answer the question based only on the following context:
                {context}[/INST]
                """,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )

    _document_chain = create_stuff_documents_chain(llm=model, prompt=prompt_template)
    _human_message_cls = HumanMessage
    _ai_message_cls = AIMessage


def _get_configured_temperature() -> float:
    """Return the Ollama temperature configured via environment settings."""

    raw_value = os.getenv(OLLAMA_TEMPERATURE_ENV)
    if raw_value is None or raw_value == "":
        return DEFAULT_TEMPERATURE

    try:
        return float(raw_value)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(
            f"Invalid temperature '{raw_value}' defined in {OLLAMA_TEMPERATURE_ENV}."
        ) from exc


def query_rag(message: ChatMessage, session_id: str = "") -> str:
    """
    Query a Retrieval-Augmented Generation (RAG) system using Chroma database and Ollama models.

    :param message: ChatMessage The text to query the RAG system with.
    :param session_id: str Session identifier.
    :return str
    """

    _ensure_initialized()

    if session_id not in chat_history:
        chat_history[session_id] = []

    response_text = _document_chain.invoke(
        {
            "context": _db.similarity_search(message.question, k=3),
            "question": message.question,
            "chat_history": chat_history[session_id],
        }
    )

    chat_history[session_id].append(_human_message_cls(content=message.question))
    chat_history[session_id].append(_ai_message_cls(content=response_text))

    return response_text
