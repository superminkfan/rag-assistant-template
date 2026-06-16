"""Shared settings for the local RAG assistant."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATHS = (
    PROJECT_ROOT / "config.yaml",
    Path.home() / ".rag-assistant" / "config.yaml",
)
DEFAULT_ARTIFACTS_ROOT = Path.home() / ".rag-assistant" / "artifacts"
DEFAULT_DB_PATH = DEFAULT_ARTIFACTS_ROOT / "chroma"
DEFAULT_JIRA_OUTPUT_ROOT = DEFAULT_ARTIFACTS_ROOT / "jira" / "export"
DEFAULT_OLLAMA_MODEL = "llama3.2:latest"
DEFAULT_EMBEDDING_MODEL = "mxbai-embed-large"
DEFAULT_TEMPERATURE = 0.1
OLLAMA_TEMPERATURE_ENV = "OLLAMA_TEMPERATURE"
DEFAULT_VECTOR_K = 6
DEFAULT_KEYWORD_K = 8
DEFAULT_FINAL_K = 6
