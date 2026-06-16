"""Ollama adapters for generation and embeddings."""

from __future__ import annotations


class OllamaLLMAdapter:
    """Expose an Ollama model through the application LLM port."""

    def __init__(self, *, model: str, temperature: float) -> None:
        from langchain_ollama import OllamaLLM

        self._client = OllamaLLM(model=model, temperature=temperature)

    def generate(self, prompt: str) -> str:
        return str(self._client.invoke(prompt))


class OllamaEmbeddingsAdapter:
    """Expose Ollama embeddings through the application embeddings port."""

    def __init__(self, *, model: str) -> None:
        from langchain_ollama import OllamaEmbeddings

        self._client = OllamaEmbeddings(model=model)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)
