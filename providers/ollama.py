import os
from typing import Dict, List

from models.index import ChatMessage


CHROMA_PATH = "./db_metadata_v5"
SIMILARITY_K_ENV_VAR = "OLLAMA_SIMILARITY_K"
DEFAULT_SIMILARITY_K = 3

_db = None
_document_chain = None
_human_message_cls = None
_ai_message_cls = None
chat_history: Dict[str, List[object]] = {}

DEFAULT_CHAT_HISTORY_WINDOW = 20


def _configured_history_window() -> int:
    """Resolve the chat history window size from the environment."""

    value = os.getenv("OLLAMA_CHAT_HISTORY_WINDOW")
    if not value:
        return DEFAULT_CHAT_HISTORY_WINDOW

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_CHAT_HISTORY_WINDOW

    return parsed if parsed > 0 else DEFAULT_CHAT_HISTORY_WINDOW


CHAT_HISTORY_WINDOW = _configured_history_window()


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

    model = OllamaLLM(model="llama3.2:latest", temperature=0.1)
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
                Support statements with bracketed, numbered citations (e.g., [1], [2]) that correspond to the retrieved context snippets.
                When an answer requires multiple steps, lay them out as an ordered list or clearly labeled sequence of steps.
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

    history = chat_history[session_id]

    similarity_k = _resolve_similarity_k()
  
    context_documents = _db.similarity_search(message.question, k=similarity_k)

    if not context_documents:
        return "Hmm, I am not sure. Let me check and get back to you."
      
    response_text = _document_chain.invoke(
        {
            "context": context_documents,
            "question": message.question,
            "chat_history": history,
        }
    )

    history.append(_human_message_cls(content=message.question))
    history.append(_ai_message_cls(content=response_text))

    _trim_history_window(history)

    return response_text

  
def _trim_history_window(history: List[object]) -> None:
    """Trim the history list in-place to respect the configured window size."""

    window = CHAT_HISTORY_WINDOW
    if window <= 0:
        return

    length = len(history)
    if length <= window:
        return

    # Remove the oldest messages while keeping the ordering and ensuring
    # at least the most recent exchange (human + AI) remains available.
    to_remove = length - window
    if to_remove % 2 != 0:
        to_remove += 1

    # Always keep at least the most recent human/AI pair when trimming.
    max_removal = max(0, length - 2)
    to_remove = min(to_remove, max_removal)

    if to_remove > 0:
        del history[:to_remove]

        
def _resolve_similarity_k() -> int:
    """Resolve the number of documents to return from the similarity search."""

    raw_value = os.getenv(SIMILARITY_K_ENV_VAR)
    if raw_value is None:
        return DEFAULT_SIMILARITY_K

    try:
        parsed_value = int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_SIMILARITY_K

    return parsed_value if parsed_value > 0 else DEFAULT_SIMILARITY_K
