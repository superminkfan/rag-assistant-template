"""Ingest Javadoc comments into a Chroma vector store."""

import argparse
import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Iterator

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = str((BASE_DIR / "../db_metadata_v5").resolve())
DEFAULT_DATA_PATH = (BASE_DIR / "../data").resolve()

JAVADOC_PATTERN = re.compile(r"/\*\*(?:.|\n)*?\*/", re.MULTILINE)

global_unique_hashes: set[str] = set()


def walk_java_files(base_path: Path) -> Iterator[Path]:
    """Yield paths to .java files under ``base_path`` recursively."""

    for root, _dirs, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith(".java"):
                yield Path(root, file_name)


def hash_text(text: str) -> str:
    """Return the SHA-256 hash of ``text``."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean_javadoc(raw_comment: str) -> str:
    """Strip comment markers from a raw Javadoc block."""

    text = raw_comment
    if text.startswith("/**"):
        text = text[3:]
    if text.endswith("*/"):
        text = text[:-2]

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("*"):
            stripped = stripped[1:]
            if stripped.startswith(" "):
                stripped = stripped[1:]
        cleaned_lines.append(stripped.rstrip())

    return "\n".join(cleaned_lines).strip()


def _extract_symbol(source: str, comment_end: int) -> str:
    """Return the first non-empty line after a Javadoc comment."""

    trailing_text = source[comment_end:]
    for line in trailing_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def load_javadoc_documents(base_path: Path) -> list[Document]:
    """Parse all Javadoc blocks under ``base_path`` into Documents."""

    documents: list[Document] = []
    for java_file in walk_java_files(base_path):
        try:
            source = java_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = java_file.read_text(encoding="utf-8", errors="ignore")

        for match in JAVADOC_PATTERN.finditer(source):
            raw_comment = match.group(0)
            cleaned = _clean_javadoc(raw_comment)
            if not cleaned:
                continue
            symbol = _extract_symbol(source, match.end())
            documents.append(
                Document(
                    page_content=cleaned,
                    metadata={
                        "source": str(java_file.resolve()),
                        "symbol": symbol,
                    },
                )
            )

    return documents


def split_documents(
    documents: list[Document], chunk_size: int, chunk_overlap: int
) -> list[Document]:
    """Split Javadoc comments while keeping metadata intact."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split {len(documents)} comments into {len(chunks)} chunks.")

    unique_chunks: list[Document] = []
    for chunk in chunks:
        chunk_hash = hash_text(chunk.page_content)
        if chunk_hash in global_unique_hashes:
            continue
        global_unique_hashes.add(chunk_hash)
        unique_chunks.append(chunk)

    print(f"Unique chunks equals {len(unique_chunks)}.")
    return unique_chunks


def save_to_chroma(chunks: list[Document], reset: bool = False) -> None:
    """Persist chunks to Chroma with Ollama embeddings."""

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

    if reset and os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    if os.path.exists(CHROMA_PATH):
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
        )
        db.add_documents(chunks)
    else:
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH,
        )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


def generate_data_store(
    base_path: Path, chunk_size: int, chunk_overlap: int, reset: bool = False
) -> None:
    """Extract, split, and store Javadoc comments."""

    documents = load_javadoc_documents(base_path)
    if not documents:
        print("No Javadoc comments found. Nothing to ingest.")
        return

    chunks = split_documents(documents, chunk_size, chunk_overlap)
    save_to_chroma(chunks, reset=reset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest Javadoc comments into a Chroma vector store.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Maximum number of characters in each chunk (default: 800)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Number of overlapping characters between chunks (default: 100)",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Directory containing Java source files (default: ../data)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="If set, delete the existing Chroma database before ingesting.",
    )

    args = parser.parse_args()

    if args.chunk_size <= 0:
        parser.error("--chunk-size must be a positive integer")
    if args.chunk_overlap < 0:
        parser.error("--chunk-overlap must be zero or a positive integer")
    if args.chunk_overlap >= args.chunk_size:
        parser.error("--chunk-overlap must be smaller than --chunk-size")

    data_path = args.data_path.resolve()
    if not data_path.exists():
        parser.error(f"--data-path {data_path} does not exist")
    if not data_path.is_dir():
        parser.error(f"--data-path {data_path} is not a directory")

    generate_data_store(
        data_path,
        args.chunk_size,
        args.chunk_overlap,
        reset=args.reset,
    )
