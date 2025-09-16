"""Convenience helpers for running Retrieval-Augmented Generation (RAG) queries.

This module keeps a lightweight interface around :func:`providers.ollama.query_rag`
so that developers can experiment with the pipeline from the command line.  The
original FastAPI application has been removed, but importing :mod:`main` still
provides a simple entry point for issuing questions against the RAG stack.
"""

from __future__ import annotations

import argparse
from typing import Optional

from models.index import ChatMessage
from providers.ollama import query_rag


def run_query(question: str, chat_id: str = "") -> str:
    """Execute a single RAG query and return the generated response."""

    return query_rag(ChatMessage(question=question), session_id=chat_id)


def run_cli(argv: Optional[list[str]] = None) -> int:
    """Launch a small command-line interface for ad-hoc queries.

    Parameters
    ----------
    argv:
        Optional list of command-line arguments.  When ``None`` (the default),
        :data:`sys.argv` is used instead.

    Returns
    -------
    int
        Exit code suitable for ``sys.exit``.
    """

    parser = argparse.ArgumentParser(description="Query the RAG knowledge base")
    parser.add_argument("question", help="User question to send to the RAG pipeline")
    parser.add_argument(
        "--chat-id",
        default="",
        help="Identifier for the conversation so that history can be preserved",
    )
    args = parser.parse_args(argv)

    print(run_query(args.question, chat_id=args.chat_id))
    return 0


if __name__ == "__main__":  # pragma: no cover - thin CLI wrapper
    raise SystemExit(run_cli())
