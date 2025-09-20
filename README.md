# RAG Assistant Template

## Overview
This repository provides a flexible Retrieval-Augmented Generation (RAG) assistant that can be
powered by any documentation set you load into the bundled vector store.  Documents are stored in a
persistent [Chroma](https://www.trychroma.com/) database (`db_metadata_v5/`), and responses are
generated with local [Ollama](https://ollama.com/) models via LangChain.  The `scripts/` directory
includes ingestion helpers for both Markdown (`ingest.py`) and AsciiDoc (`ingest_adoc.py`) sources so
you can rebuild the knowledge base from your own materials.

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
  pip install langchain langchain-community langchain-chroma langchain-ollama python-telegram-bot pytest
  ```

## Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-org>/rag-assistant-template.git
   cd rag-assistant-template
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
   [Requirements](#requirements) section manually (including
   `python-telegram-bot`).

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
- **Environment variables** – tune the RAG provider without touching code:
  - `OLLAMA_TEMPERATURE` – optional control for the sampling temperature
    supplied to the local Ollama model.  If unset the provider defaults to
    `0.1`, which keeps answers focused and deterministic.
  - `OLLAMA_SIMILARITY_K` – sets how many documents are returned from the
    similarity search per question.  Leaving it unset keeps the default value
    of `3`, which balances recall with concise context windows.
  - `OLLAMA_CHAT_HISTORY_WINDOW` – caps how many past chat messages (human and
    AI) are retained per conversation.  The default is `20`, ensuring recent
    context is preserved while old exchanges are trimmed automatically.

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
├── data/                # User-supplied source docs; create/provide before running ingest scripts
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
- Use `scripts/ingest.py` (Markdown) or `scripts/ingest_adoc.py` (AsciiDoc) to
  rebuild the vector store whenever new documentation needs to be indexed.  Both
  scripts look for content in `../data` by default; ensure that directory exists
  or provide an alternative with `--data-path /path/to/sources` before running
  them.
