# Langchain dependencies
import argparse
import hashlib
import os
import shutil
import re
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings


# Paths resolved relative to this file so the script works from any cwd
BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = str((BASE_DIR / "../db_metadata_v5").resolve())
DEFAULT_DATA_PATH = (BASE_DIR / "../data").resolve()
global_unique_hashes = set()


def walk_through_files(path, file_extensions=(".adoc", ".md")):
    """
    Yield file paths under `path` that end with any of the given `file_extensions`.
    By default, targets AsciiDoc (.adoc). Add .md for mixed repos as needed.
    """
    for (dir_path, dir_names, filenames) in os.walk(path):
        for filename in filenames:
            if filename.endswith(file_extensions):
                yield os.path.join(dir_path, filename)


def preprocess_tabs_content(text: str) -> str:
    """Collapse AsciiDoc tab blocks to Unix-only content.

    The Antora tab syntax looks like::

        [tabs]
        ====                              or  --
        tab:Unix[]
        --
        <content>
        --
        tab:Windows[]
        --
        <content>
        --
        ====                              or  --

    This helper removes the surrounding tab scaffolding, keeps only
    ``tab:Unix[]`` sections, and deduplicates identical Unix content.
    """

    had_trailing_newline = text.endswith("\n")
    lines = text.splitlines()
    processed_lines: list[str] = []
    i = 0

    def _consume_tabs_block(start_index: int) -> tuple[list[str], int]:
        block_lines: list[str] = []
        idx = start_index + 1

        # Skip optional blank lines after [tabs]
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1

        if idx >= len(lines):
            return [lines[start_index]], start_index + 1

        end_token = lines[idx].strip()
        if end_token not in {"====", "--"}:
            return [lines[start_index]], start_index + 1

        idx += 1
        while idx < len(lines):
            if lines[idx].strip() == end_token:
                idx += 1
                break
            block_lines.append(lines[idx])
            idx += 1
        else:
            # Unterminated block; fall back to original text
            return lines[start_index:idx], idx

        processed_block_lines = _process_tab_sections(block_lines)
        return processed_block_lines, idx

    def _process_tab_sections(block_body: list[str]) -> list[str]:
        sections: list[tuple[str, list[str]]] = []
        current_tab: str | None = None
        collecting = False
        buffer: list[str] = []

        for line in block_body:
            stripped = line.strip()
            tab_match = re.match(r"tab:([^\[]+)\[\]", stripped)
            if tab_match:
                if collecting and current_tab is not None:
                    sections.append((current_tab, buffer))
                current_tab = tab_match.group(1)
                collecting = False
                buffer = []
                continue

            if stripped == "--":
                if current_tab is None:
                    continue
                if collecting:
                    sections.append((current_tab, buffer))
                    collecting = False
                    current_tab = None
                    buffer = []
                else:
                    collecting = True
                    buffer = []
                continue

            if collecting and current_tab is not None:
                buffer.append(line)

        if collecting and current_tab is not None:
            sections.append((current_tab, buffer))

        unix_sections: list[str] = []
        seen_keys: set[str] = set()
        for tab_name, tab_lines in sections:
            if tab_name.strip().lower() != "unix":
                continue
            text_block = "\n".join(tab_lines)
            key = "\n".join(line.rstrip() for line in tab_lines).strip()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unix_sections.append(text_block)

        output_lines: list[str] = []
        for idx, section in enumerate(unix_sections):
            section_lines = section.split("\n") if section else [""]
            if idx > 0 and output_lines and output_lines[-1] != "":
                output_lines.append("")
            output_lines.extend(section_lines)

        return output_lines

    while i < len(lines):
        if lines[i].strip() == "[tabs]":
            replacement, next_index = _consume_tabs_block(i)
            processed_lines.extend(replacement)
            i = next_index
        else:
            processed_lines.append(lines[i])
            i += 1

    result = "\n".join(processed_lines)
    if had_trailing_newline:
        result += "\n"
    return result


def load_documents(
    data_path: Path, file_extensions: tuple[str, ...] | None = None
):
    """
    Load documents from the specified directory.

    Returns:
        List[Document]
    """
    documents = []
    extensions = file_extensions or (".adoc", ".md")
    for f_name in walk_through_files(str(data_path), file_extensions=extensions):
        # TextLoader safely reads both .adoc and .md files
        document_loader = TextLoader(f_name, encoding="utf-8")
        loaded = document_loader.load()
        for doc in loaded:
            cleaned_content = preprocess_tabs_content(doc.page_content)
            doc.page_content = cleaned_content
        documents.extend(loaded)
    return documents


def hash_text(text: str) -> str:
    # Generate a hash value for the text using SHA-256
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_text(documents: list[Document], chunk_size: int, chunk_overlap: int):
    """
    Split text into chunks with AsciiDoc-aware separators to avoid breaking code blocks and tables.

    Priorities (from largest to smallest granularity):
      - AsciiDoc headings (=, ==, ===, …)
      - Table boundaries |=== ... |===
      - Code blocks [source]\n---- ... ---- and listing blocks .... ... ....
      - Paragraphs
      - Lists
      - Lines, words, characters
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        # Order matters: earlier separators are preferred split positions
        separators=[
            "\n= ", "\n== ", "\n=== ", "\n==== ", "\n===== ",  # AsciiDoc headings
            "\n|===\n",                                        # AsciiDoc table boundaries
            "\n[source",                                       # Start of a block with [source,java] attributes, etc.
            "\n----\n",                                        # AsciiDoc code fences
            "\n....\n",                                        # AsciiDoc listing blocks
            "\n\n====\n\n",                                    # Section delimiters (occasionally used)
            "\n\n***\n\n", "\n\n---\n\n", "\n\n____\n\n",      # Horizontal or block rules
            "\n\n",                                            # Paragraphs
            "\n* ", "\n- ", "\n. ",                            # Lists or numbered items
            "\n",                                              # Lines
            " ",                                               # Words
            "",                                                # Characters
        ],
        # Preserve whitespace to keep table and listing structure intact
        keep_separator=False,
        strip_whitespace=False,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Deduplicate by content hash
    unique_chunks = []
    for chunk in chunks:
        # Optional place to normalize leading or trailing whitespace if needed
        content = chunk.page_content
        chunk_hash = hash_text(content)
        if chunk_hash not in global_unique_hashes:
            unique_chunks.append(chunk)
            global_unique_hashes.add(chunk_hash)

    print(f"Unique chunks equals {len(unique_chunks)}.")
    return unique_chunks


def save_to_chroma(chunks: list[Document], reset: bool = False):
    """
    Save chunks to a Chroma DB with Ollama embeddings.
    """
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
        # Create a new Chroma database from the documents using local Ollama embeddings
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH,
        )

    # Persist the database to disk
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


def generate_data_store(
    chunk_size: int,
    chunk_overlap: int,
    data_path: Path,
    file_extensions: tuple[str, ...] | None = None,
    reset: bool = False,
):
    """
    Build a Chroma vector DB from AsciiDoc/Markdown documents with AsciiDoc-aware splitting.
    """
    documents = load_documents(data_path, file_extensions=file_extensions)
    chunks = split_text(documents, chunk_size, chunk_overlap)
    save_to_chroma(chunks, reset=reset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest .adoc/.md documents (AsciiDoc-friendly) into a Chroma vector store."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,  # Slightly higher default to accommodate large tables/code blocks
        help="Maximum number of characters in each chunk (default: 1200)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Number of overlapping characters between chunks (default: 150)",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Directory containing .adoc/.md docs to ingest (default: ../data)",
    )
    parser.add_argument(
        "--only-adoc",
        action="store_true",
        help="If set, only ingest .adoc files (ignore .md).",
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

    file_extensions: tuple[str, ...] | None = None
    if args.only_adoc:
        file_extensions = (".adoc",)

    generate_data_store(
        args.chunk_size,
        args.chunk_overlap,
        data_path,
        file_extensions=file_extensions,
        reset=args.reset,
    )
