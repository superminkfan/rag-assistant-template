"""Command line interface for the local RAG assistant."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from rag_assistant.config import AppConfig, load_config, source_path_for_type
from rag_assistant.factory import build_local_rag, build_local_vector_store
from rag_assistant.indexing import ingest_source
from rag_assistant.inspection import (
    format_index_summary,
    format_source_summary,
    inspect_index,
    inspect_source,
)
from rag_assistant.rag import analyze_incident, ask


def print_progress(message: str) -> None:
    """Print long-running progress immediately in CLI pipelines."""

    print(message, flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rag-assistant")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to YAML config (default lookup: ./config.yaml, then ~/.rag-assistant/config.yaml)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to the Chroma database (overrides config paths.db_path)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest documentation into Chroma")
    ingest_parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Documentation source path (defaults to config path for source type)",
    )
    ingest_parser.add_argument(
        "--source-type",
        default="datagrid-docs",
        choices=["datagrid-docs", "ignite-docs", "jira-snapshot"],
        help="Source loader type",
    )
    ingest_parser.add_argument("--chunk-size", type=int, default=1200)
    ingest_parser.add_argument("--chunk-overlap", type=int, default=180)
    ingest_parser.add_argument("--limit", type=int, default=None, help="Limit source docs for smoke tests")
    ingest_parser.add_argument("--batch-size", type=int, default=64)
    ingest_parser.add_argument("--reset", action="store_true")
    ingest_parser.add_argument(
        "--replace-source-type",
        action="store_true",
        help="Delete existing chunks with the same source_type before ingesting",
    )

    ask_parser = subparsers.add_parser("ask", help="Ask a question against the local index")
    ask_parser.add_argument("question", nargs="+", help="Question text")

    incident_parser = subparsers.add_parser(
        "analyze-incident",
        help="Analyze an incident text file against the local index",
    )
    incident_parser.add_argument("path", type=Path, help="Path to a text file with incident details")

    inspect_parser = subparsers.add_parser(
        "inspect-index",
        help="Inspect collections and metadata in the local Chroma index",
    )
    inspect_parser.add_argument(
        "--sample-limit",
        type=int,
        default=None,
        help="Only inspect this many metadata rows per collection",
    )

    source_parser = subparsers.add_parser(
        "inspect-source",
        help="Dry-run a source loader and chunker without embedding",
    )
    source_parser.add_argument("--source", type=Path, default=None)
    source_parser.add_argument(
        "--source-type",
        required=True,
        choices=["datagrid-docs", "ignite-docs", "jira-snapshot"],
    )
    source_parser.add_argument("--chunk-size", type=int, default=1200)
    source_parser.add_argument("--chunk-overlap", type=int, default=180)
    source_parser.add_argument("--limit", type=int, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    db_path = args.db_path or config.paths.db_path

    if args.command == "ingest":
        source_path = _resolve_source_path(parser, config, args.source_type, args.source)
        vector_store = build_local_vector_store(
            db_path=db_path,
            embedding_model=config.ollama.embedding_model,
            reset=args.reset,
        )
        stats = ingest_source(
            source_path,
            vector_store=vector_store,
            source_type=args.source_type,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            limit=args.limit,
            batch_size=args.batch_size,
            replace_source_type=args.replace_source_type,
            progress=print_progress,
        )
        print(
            f"Ingested {stats['documents']} documents into {stats['chunks']} chunks at {stats['db_path']}."
        )
        return 0

    if args.command == "ask":
        components = build_local_rag(
            db_path=db_path,
            model=config.ollama.model,
            embedding_model=config.ollama.embedding_model,
            temperature=config.ollama.temperature,
            vector_k=config.retrieval.vector_k,
            keyword_k=config.retrieval.keyword_k,
            final_k=config.retrieval.final_k,
        )
        print(
            ask(
                " ".join(args.question),
                llm=components.llm,
                retriever=components.retriever,
            )
        )
        return 0

    if args.command == "analyze-incident":
        incident_text = args.path.read_text(encoding="utf-8")
        components = build_local_rag(
            db_path=db_path,
            model=config.ollama.model,
            embedding_model=config.ollama.embedding_model,
            temperature=config.ollama.temperature,
            vector_k=config.retrieval.vector_k,
            keyword_k=config.retrieval.keyword_k,
            final_k=config.retrieval.final_k,
        )
        print(
            analyze_incident(
                incident_text,
                llm=components.llm,
                retriever=components.retriever,
            )
        )
        return 0

    if args.command == "inspect-index":
        print(format_index_summary(inspect_index(db_path, sample_limit=args.sample_limit)))
        return 0

    if args.command == "inspect-source":
        source_path = _resolve_source_path(parser, config, args.source_type, args.source)
        print(
            format_source_summary(
                inspect_source(
                    source_path,
                    source_type=args.source_type,
                    chunk_size=args.chunk_size,
                    chunk_overlap=args.chunk_overlap,
                    limit=args.limit,
                )
            )
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _resolve_source_path(
    parser: argparse.ArgumentParser,
    config: AppConfig,
    source_type: str,
    explicit_source: Path | None,
) -> Path:
    if explicit_source is not None:
        return explicit_source

    configured_source = source_path_for_type(config, source_type)
    if configured_source is not None:
        return configured_source

    if source_type == "datagrid-docs":
        parser.error("set paths.datagrid_docs in config or pass --source")
    if source_type == "ignite-docs":
        parser.error("set paths.ignite_docs in config or pass --source")
    parser.error("set jira.output_root in config or pass --source")
    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
