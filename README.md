# RAG Project from DataGrid Docs

## Overview
This repository contains utilities for querying a Retrieval-Augmented Generation (RAG) pipeline that was built from DataGrid
product documentation.  Documents are stored in a persistent
[Chroma](https://www.trychroma.com/) vector database (bundled in `db_metadata_v5/`),
and responses are generated with local [Ollama](https://ollama.com/) models via LangChain.

The former FastAPI wrapper has been removed in favour of direct access to the
underlying RAG provider.  You can now interact with the system either by importing
`run_query` or by using the lightweight command-line interface exposed by
`main.py`.

## Requirements
- Python 3.10 or higher.
- Access to an Ollama runtime with the `llama3.2:latest` and
  `mxbai-embed-large` models installed.
- The dependencies listed below (they can be installed into a virtual environment):
  ```bash
  pip install langchain langchain-community langchain-chroma langchain-ollama pytest
  ```

## Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-org>/ragProjectFromDataGridDocs.git
   cd ragProjectFromDataGridDocs
   ```
2. **Create and activate a virtual environment** (optional but recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\\Scripts\\activate`
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   If you prefer not to use `requirements.txt`, install the packages listed in the
   [Requirements](#requirements) section manually.

## Usage
Run ad-hoc queries with the CLI:
```bash
python -m main "How do I configure the agent?" --chat-id demo
```

Alternatively, interact with the provider directly from Python:
```python
from main import run_query

print(run_query("How do I configure the agent?", chat_id="demo"))
```

The `chat_id` parameter lets you preserve conversation state across multiple
queries.  Provide the same identifier to maintain a running dialogue.

## Configuration
- `db_metadata_v5/` – directory that stores the persistent Chroma database.
  Replace or rebuild it with your own knowledge base if required.

## Running tests
The project uses [pytest](https://docs.pytest.org/) for automated testing.
After installing dependencies run:
```bash
pytest
```
The included tests exercise the `query_rag` function directly without spinning
up any web framework components.

## Project structure
```
.
├── data/                # Source documentation used to build the vector store
├── db_metadata_v5/      # Persisted Chroma database files
├── main.py              # CLI helpers for interacting with the RAG provider
├── models/              # Data models shared across the project
├── providers/           # Integration with the Ollama-based RAG provider
├── scripts/             # Utilities for scraping and ingesting documentation into Chroma
└── tests/               # Pytest suite exercising the RAG provider
```

## Development tips
- The Ollama-backed RAG provider is loaded lazily.  If the required LangChain
  modules are not installed, automated tests can still run by mocking the
  provider.
- Use `scripts/ingest.py` to rebuild the vector store whenever new documentation
  is added to `data/`.
