# Langchain dependencies
import argparse
import hashlib
import os
import shutil
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import MarkdownTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings


# Paths resolved relative to this file so the script works from any cwd
BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = str((BASE_DIR / "../db_metadata_v5").resolve())
DATA_PATH = str((BASE_DIR / "../docs").resolve())
global_unique_hashes = set()


def walk_through_files(path, file_extension='.md'):
    for (dir_path, dir_names, filenames) in os.walk(path):
        for filename in filenames:
            if filename.endswith(file_extension):
                yield os.path.join(dir_path, filename)


def load_documents():
    """
    Load documents from the specified directory
    Returns:
    List of Document objects:
    """
    documents = []
    for f_name in walk_through_files(DATA_PATH):
        document_loader = TextLoader(f_name, encoding="utf-8")
        documents.extend(document_loader.load())

    return documents


def hash_text(text):
    # Generate a hash value for the text using SHA-256
    hash_object = hashlib.sha256(text.encode())
    return hash_object.hexdigest()


def split_text(documents: list[Document], chunk_size: int, chunk_overlap: int):
    """
    Split the text content of the given list of Document objects into smaller chunks.

    Args:
        documents (list[Document]): List of Document objects containing text content to split.
        chunk_size (int): Maximum number of characters allowed in a chunk.
        chunk_overlap (int): Number of characters to overlap between chunks.

    Returns:
        list[Document]: List of Document objects representing the split text chunks.
    """
    text_splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,  # Size of each chunk in characters
        chunk_overlap=chunk_overlap,  # Overlap between consecutive chunks
        length_function=len,  # Function to compute the length of the text
    )

    # Split documents into smaller chunks using text splitter
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Deduplication mechanism
    unique_chunks = []
    for chunk in chunks:
        chunk_hash = hash_text(chunk.page_content)
        if chunk_hash not in global_unique_hashes:
            unique_chunks.append(chunk)
            global_unique_hashes.add(chunk_hash)

    # Print example of page content and metadata for a chunk
    print(f"Unique chunks equals {len(unique_chunks)}.")
    # print(unique_chunks[:-5])

    return unique_chunks  # Return the list of split text chunks


def save_to_chroma(chunks: list[Document]):
    """
    Save the given list of Document objects to a Chroma database.
    Args:
    chunks (list[Document]): List of Document objects representing text chunks to save.
    Returns:
    None
    """
    # Clear out the existing database directory if it exists
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new Chroma database from the documents using OpenAI embeddings
    db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model="mxbai-embed-large"),
        persist_directory=CHROMA_PATH
    )

    # Persist the database to disk
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


def generate_data_store(chunk_size: int, chunk_overlap: int):
    """
    Function to generate a Chroma vector database from documents using the provided chunk settings.

    Args:
        chunk_size (int): Maximum number of characters allowed in a chunk.
        chunk_overlap (int): Number of characters to overlap between chunks.
    """
    documents = load_documents()  # Load documents from a source
    chunks = split_text(documents, chunk_size, chunk_overlap)  # Split documents into manageable chunks
    save_to_chroma(chunks)  # Save the processed data to a data store


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest markdown documents into a Chroma vector store.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Maximum number of characters in each chunk (default: 500)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Number of overlapping characters between chunks (default: 100)",
    )

    args = parser.parse_args()

    if args.chunk_size <= 0:
        parser.error("--chunk-size must be a positive integer")
    if args.chunk_overlap < 0:
        parser.error("--chunk-overlap must be zero or a positive integer")
    if args.chunk_overlap >= args.chunk_size:
        parser.error("--chunk-overlap must be smaller than --chunk-size")

    generate_data_store(args.chunk_size, args.chunk_overlap)
