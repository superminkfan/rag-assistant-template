"""Composition root for the default local RAG stack."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag_assistant.adapters.chroma import ChromaVectorStoreAdapter
from rag_assistant.adapters.ollama import OllamaEmbeddingsAdapter, OllamaLLMAdapter
from rag_assistant.adapters.retrieval import HybridRetriever
from rag_assistant.ports import Embeddings, LLM, Retriever, VectorStore
from rag_assistant.settings import (
    DEFAULT_DB_PATH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_FINAL_K,
    DEFAULT_KEYWORD_K,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_VECTOR_K,
)


@dataclass(frozen=True)
class LocalRagComponents:
    """Concrete dependencies used by the local CLI configuration."""

    llm: LLM
    embeddings: Embeddings
    vector_store: VectorStore
    retriever: Retriever


def build_local_vector_store(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    reset: bool = False,
) -> VectorStore:
    """Build the default local embedding and Chroma adapters."""

    embeddings = OllamaEmbeddingsAdapter(model=embedding_model)
    return ChromaVectorStoreAdapter(
        db_path=db_path,
        embeddings=embeddings,
        reset=reset,
    )


def build_local_rag(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    model: str = DEFAULT_OLLAMA_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    vector_k: int = DEFAULT_VECTOR_K,
    keyword_k: int = DEFAULT_KEYWORD_K,
    final_k: int = DEFAULT_FINAL_K,
) -> LocalRagComponents:
    """Build generation, storage, and retrieval adapters for local execution."""

    embeddings = OllamaEmbeddingsAdapter(model=embedding_model)
    vector_store = ChromaVectorStoreAdapter(db_path=db_path, embeddings=embeddings)
    retriever = HybridRetriever(
        vector_store,
        vector_k=vector_k,
        keyword_k=keyword_k,
        final_k=final_k,
    )
    llm = OllamaLLMAdapter(model=model, temperature=temperature)
    return LocalRagComponents(
        llm=llm,
        embeddings=embeddings,
        vector_store=vector_store,
        retriever=retriever,
    )
