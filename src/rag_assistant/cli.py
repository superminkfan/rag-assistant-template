"""Command line interface for the local RAG assistant."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import threading
import time
from typing import Callable, TypeVar

from rag_assistant.config import AppConfig, load_config, source_path_for_type
from rag_assistant.confluence import (
    build_public_session,
    collect_offline_pages,
    collect_public_pages,
    write_snapshot as write_confluence_snapshot,
)
from rag_assistant.factory import build_local_rag, build_local_vector_store
from rag_assistant.evaluation import (
    evaluate_retrieval,
    format_evaluation_summary,
    load_evaluation_cases,
)
from rag_assistant.indexing import ingest_source
from rag_assistant.inspection import (
    format_index_summary,
    format_source_summary,
    inspect_index,
    inspect_source,
)
from rag_assistant.rag import analyze_incident, ask
from rag_assistant.settings import DEFAULT_RETRIEVAL_EVALUATION_PATH


T = TypeVar("T")
SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
SOURCE_TYPES = [
    "datagrid-docs",
    "ignite-docs",
    "jira-snapshot",
    "confluence-snapshot",
    "ignite-firefighter-tree",
    "ignite-firefighter-notes",
    "stackoverflow-kb",
    "ignite-user-mailing-list",
]


def print_progress(message: str) -> None:
    """Print long-running progress immediately in CLI pipelines."""

    print(message, flush=True)


def run_with_spinner(
    operation: Callable[[], T],
    *,
    message: str = "Assistant is thinking",
    stream=None,
) -> tuple[T, float]:
    """Run an operation while showing activity in an interactive terminal."""

    output = stream or sys.stderr
    stop = threading.Event()
    started_at = time.perf_counter()
    spinner_thread: threading.Thread | None = None

    if output.isatty():
        spinner_thread = threading.Thread(
            target=_animate_spinner,
            args=(stop, message, output),
            daemon=True,
        )
        spinner_thread.start()

    try:
        result = operation()
    finally:
        stop.set()
        if spinner_thread is not None:
            spinner_thread.join()
            _clear_status_line(message, output)

    return result, time.perf_counter() - started_at


def _animate_spinner(stop: threading.Event, message: str, stream) -> None:
    frame_index = 0
    while not stop.is_set():
        stream.write(f"\r{SPINNER_FRAMES[frame_index]} {message}")
        stream.flush()
        frame_index = (frame_index + 1) % len(SPINNER_FRAMES)
        stop.wait(0.1)


def _clear_status_line(message: str, stream) -> None:
    width = len(message) + 3
    stream.write(f"\r{' ' * width}\r")
    stream.flush()


def print_answer(answer: str, elapsed_seconds: float) -> None:
    print(answer)
    print(f"\nResponse time: {elapsed_seconds:.2f} s")


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
        choices=SOURCE_TYPES,
        help="Source loader type",
    )
    ingest_parser.add_argument("--chunk-size", type=int, default=1200)
    ingest_parser.add_argument("--chunk-overlap", type=int, default=180)
    ingest_parser.add_argument("--limit", type=int, default=None, help="Limit source docs for smoke tests")
    ingest_parser.add_argument("--batch-size", type=int, default=64)
    ingest_parser.add_argument(
        "--source-id",
        default=None,
        help="Configured Confluence snapshot id, for example sberworks",
    )
    ingest_parser.add_argument("--reset", action="store_true")
    replace_group = ingest_parser.add_mutually_exclusive_group()
    replace_group.add_argument(
        "--replace-source-type",
        action="store_true",
        help="Delete existing chunks with the same source_type before ingesting",
    )
    replace_group.add_argument(
        "--replace-source-id",
        action="store_true",
        help="Delete existing chunks with the snapshot source_id before ingesting",
    )

    snapshot_parser = subparsers.add_parser(
        "snapshot-confluence",
        help="Create an atomic snapshot from public or browser-saved Confluence pages",
    )
    snapshot_parser.add_argument(
        "--source-id",
        required=True,
        choices=["apache-ignite-design", "sberworks"],
    )
    snapshot_parser.add_argument(
        "--offline-dir",
        type=Path,
        default=None,
        help="Directory containing browser-saved HTML pages (required for sberworks)",
    )
    snapshot_parser.add_argument(
        "--seed-url",
        default=None,
        help="Override the configured public Apache Confluence seed URL",
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
        choices=SOURCE_TYPES,
    )
    source_parser.add_argument("--source-id", default=None)
    source_parser.add_argument("--chunk-size", type=int, default=1200)
    source_parser.add_argument("--chunk-overlap", type=int, default=180)
    source_parser.add_argument("--limit", type=int, default=None)

    evaluation_parser = subparsers.add_parser(
        "evaluate-retrieval",
        help="Run the bundled retrieval benchmark without LLM generation",
    )
    evaluation_parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_RETRIEVAL_EVALUATION_PATH,
    )
    evaluation_parser.add_argument("--limit", type=int, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    db_path = args.db_path or config.paths.db_path

    if args.command == "ingest":
        source_path = _resolve_source_path(
            parser,
            config,
            args.source_type,
            args.source,
            source_id=args.source_id,
        )
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
            replace_source_id=args.replace_source_id,
            progress=print_progress,
        )
        print(
            f"Ingested {stats['documents']} documents into {stats['chunks']} chunks at {stats['db_path']}."
        )
        return 0

    if args.command == "snapshot-confluence":
        if args.source_id == "sberworks":
            if args.offline_dir is None:
                parser.error("snapshot-confluence --source-id sberworks requires --offline-dir")
            pages = collect_offline_pages(args.offline_dir, source_id=args.source_id)
            mode = "offline-html"
            seed_url = None
        else:
            if args.offline_dir is not None:
                parser.error("--offline-dir is only supported for source-id sberworks")
            seed_url = args.seed_url or config.confluence.apache_seed_url
            pages = collect_public_pages(
                build_public_session(),
                source_id=args.source_id,
                seed_url=seed_url,
                progress=print_progress,
            )
            mode = "public-rest"
        snapshot_dir = write_confluence_snapshot(
            output_root=config.confluence.output_root,
            source_id=args.source_id,
            pages=pages,
            mode=mode,
            seed_url=seed_url,
        )
        print(f"Published Confluence snapshot with {len(pages)} pages: {snapshot_dir}")
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
        answer, elapsed_seconds = run_with_spinner(
            lambda: ask(
                " ".join(args.question),
                llm=components.llm,
                retriever=components.retriever,
            ),
        )
        print_answer(answer, elapsed_seconds)
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
        answer, elapsed_seconds = run_with_spinner(
            lambda: analyze_incident(
                incident_text,
                llm=components.llm,
                retriever=components.retriever,
            ),
        )
        print_answer(answer, elapsed_seconds)
        return 0

    if args.command == "inspect-index":
        print(format_index_summary(inspect_index(db_path, sample_limit=args.sample_limit)))
        return 0

    if args.command == "inspect-source":
        source_path = _resolve_source_path(
            parser,
            config,
            args.source_type,
            args.source,
            source_id=args.source_id,
        )
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

    if args.command == "evaluate-retrieval":
        components = build_local_rag(
            db_path=db_path,
            model=config.ollama.model,
            embedding_model=config.ollama.embedding_model,
            temperature=config.ollama.temperature,
            vector_k=config.retrieval.vector_k,
            keyword_k=config.retrieval.keyword_k,
            final_k=config.retrieval.final_k,
        )
        cases = load_evaluation_cases(args.cases)
        summary = evaluate_retrieval(
            cases,
            retriever=components.retriever,
            limit=args.limit,
        )
        print(format_evaluation_summary(summary))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _resolve_source_path(
    parser: argparse.ArgumentParser,
    config: AppConfig,
    source_type: str,
    explicit_source: Path | None,
    *,
    source_id: str | None = None,
) -> Path:
    if explicit_source is not None:
        return explicit_source

    configured_source = source_path_for_type(config, source_type, source_id)
    if configured_source is not None:
        return configured_source

    if source_type == "datagrid-docs":
        parser.error("set paths.datagrid_docs in config or pass --source")
    if source_type == "ignite-docs":
        parser.error("set paths.ignite_docs in config or pass --source")
    if source_type == "confluence-snapshot":
        parser.error("pass --source or --source-id for a Confluence snapshot")
    if source_type in {
        "ignite-firefighter-tree",
        "ignite-firefighter-notes",
        "stackoverflow-kb",
        "ignite-user-mailing-list",
    }:
        parser.error("set paths.ignite_firefighter_kb in config or pass --source")
    parser.error("set jira.output_root in config or pass --source")
    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
