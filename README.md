# RAG Project from DataGrid Docs

## Overview
This repository contains utilities for querying a Retrieval-Augmented Generation (RAG) pipeline that was built from DataGrid
product documentation.  Documents are stored in a persistent
[Chroma](https://www.trychroma.com/) vector database (bundled in `db_metadata_v5/`),
and responses are generated with local [Ollama](https://ollama.com/) models via LangChain.

The former FastAPI wrapper has been replaced with a Telegram bot entry point in
`main.py`.  The bot is the primary interface on both desktop and mobile clients,
while the underlying provider can still be reused directly from Python code when
needed.

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
Follow these steps to run the Telegram bot:

1. **Set your Telegram bot token**
   Obtain a token from [@BotFather](https://t.me/BotFather) and expose it via the
   `TELEGRAM_TOKEN` environment variable before starting the bot:
   ```bash
   export TELEGRAM_TOKEN="123456789:ABCDEF"          # Linux / macOS
   set TELEGRAM_TOKEN=123456789:ABCDEF               # Windows (Command Prompt)
   $Env:TELEGRAM_TOKEN = "123456789:ABCDEF"         # Windows (PowerShell)
   ```

2. **Install the required Ollama models**
   Ensure the Ollama runtime has the models the bot expects:
   ```bash
   ollama pull llama3.2:latest
   ollama pull mxbai-embed-large
   ```

3. **Run the bot**
   ```bash
   python main.py
   ```
   The script launches `ollama serve` automatically and begins polling for
   Telegram messages.

4. **Chat with your assistant from Telegram**
   Open a conversation with your bot from the official Telegram clients on
   desktop or mobile and start sending questions.  Conversations are scoped to
   the chat in which they are sent, so history persists naturally per user or
   group.

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
├── main.py              # Telegram bot entry point for the RAG provider
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
