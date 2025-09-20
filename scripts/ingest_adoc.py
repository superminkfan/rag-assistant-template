# Langchain dependencies
import argparse
import hashlib
import os
import shutil
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


def load_documents(data_path: Path):
    """
    Load documents from the specified directory.

    Returns:
        List[Document]
    """
    documents = []
    for f_name in walk_through_files(str(data_path)):
        # TextLoader безопасно читает и .adoc, и .md
        document_loader = TextLoader(f_name, encoding="utf-8")
        documents.extend(document_loader.load())
    return documents


def hash_text(text: str) -> str:
    # Generate a hash value for the text using SHA-256
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_text(documents: list[Document], chunk_size: int, chunk_overlap: int):
    """
    Split text into chunks with AsciiDoc-aware separators to avoid breaking code blocks and tables.

    Priorities (от более крупных к более мелким):
      - Заголовки AsciiDoc (=, ==, ===, …)
      - Границы таблиц |=== ... |===
      - Блоки кода [source]\n---- ... ---- и листинги .... ... ....
      - Абзацы
      - Списки
      - Строки, слова, символы
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        # порядок важен: первые элементы — самые желанные места разреза
        separators=[
            "\n= ", "\n== ", "\n=== ", "\n==== ", "\n===== ",  # заголовки AsciiDoc
            "\n|===\n",                                        # граница таблиц AsciiDoc
            "\n[source",                                       # начало блока с атрибутами [source,java] и т.п.
            "\n----\n",                                        # ограждение кода AsciiDoc
            "\n....\n",                                        # листинговые блоки AsciiDoc
            "\n\n====\n\n",                                    # разделители секций (иногда встречаются)
            "\n\n***\n\n", "\n\n---\n\n", "\n\n____\n\n",      # горизонтальные/блочные правила
            "\n\n",                                            # абзацы
            "\n* ", "\n- ", "\n. ",                            # списки/нумерация
            "\n",                                              # строки
            " ",                                               # слова
            "",                                                # символы
        ],
        # Бережнее к whitespace: не выпиливаем его, чтобы не терять структуру таблиц/листингов
        keep_separator=False,
        strip_whitespace=False,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Deduplicate by content hash
    unique_chunks = []
    for chunk in chunks:
        # Опционально можно слегка нормализовать пробелы в конце-начале:
        content = chunk.page_content
        chunk_hash = hash_text(content)
        if chunk_hash not in global_unique_hashes:
            unique_chunks.append(chunk)
            global_unique_hashes.add(chunk_hash)

    print(f"Unique chunks equals {len(unique_chunks)}.")
    return unique_chunks


def save_to_chroma(chunks: list[Document]):
    """
    Save chunks to a Chroma DB with Ollama embeddings.
    """
    # Clear out the existing database directory if it exists
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new Chroma database from the documents using local Ollama embeddings
    db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model="mxbai-embed-large"),
        persist_directory=CHROMA_PATH,
    )

    # Persist the database to disk
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


def generate_data_store(chunk_size: int, chunk_overlap: int, data_path: Path):
    """
    Build a Chroma vector DB from AsciiDoc/Markdown documents with AsciiDoc-aware splitting.
    """
    documents = load_documents(data_path)
    chunks = split_text(documents, chunk_size, chunk_overlap)
    save_to_chroma(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest .adoc/.md documents (AsciiDoc-friendly) into a Chroma vector store."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,  # слегка увеличил дефолт для объёмных таблиц/кода
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

    # Настроим расширения под задачу
    if args.only_adoc:
        # Перепривяжем генератор файлов к .adoc только
        def walk_only_adoc(path):
            yield from walk_through_files(path, file_extensions=(".adoc",))
        walk_through_files = walk_only_adoc  # type: ignore

    generate_data_store(args.chunk_size, args.chunk_overlap, data_path)
