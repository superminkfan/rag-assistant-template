# RAG Project from DataGrid Docs

## Overview
This repository contains a FastAPI application that exposes a Retrieval-Augmented Generation (RAG) chat endpoint.  Documents are stored in a persistent [Chroma](https://www.trychroma.com/) vector database (bundled in `db_metadata_v5/`), and responses are generated with local [Ollama](https://ollama.com/) models via LangChain.

The service currently exposes two endpoints:

- `GET /` – health-check style endpoint that returns a static greeting.
- `POST /chat/{chat_id}` – accepts a JSON payload with a `question` field, forwards it to the RAG pipeline, and returns the generated answer.  Conversations are grouped by `chat_id` so that each session maintains its own history.

## Requirements
- Python 3.10 or higher.
- Access to an Ollama runtime with the `llama3.2:latest` and `mxbai-embed-large` models installed.
- The dependencies listed below (they can be installed into a virtual environment):
  ```bash
  pip install fastapi uvicorn[standard] langchain langchain-community langchain-chroma langchain-ollama pytest
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
   If you prefer not to use `requirements.txt`, install the packages listed in the [Requirements](#requirements) section manually.

## Configuration
- `ALLOWED_ORIGINS` – optional comma-separated list of allowed CORS origins. When not provided, local development origins (e.g. `http://localhost:3000`) are permitted by default.
- `db_metadata_v5/` – directory that stores the persistent Chroma database.  Replace or rebuild it with your own knowledge base if required.

## Running the API server
Use [uvicorn](https://www.uvicorn.org/) to launch the FastAPI application:
```bash
uvicorn main:app --reload
```
The application will be available at `http://127.0.0.1:8000`.  The interactive API docs can be accessed at `http://127.0.0.1:8000/docs`.

## Running tests
The project uses [pytest](https://docs.pytest.org/) for automated testing.  After installing dependencies run:
```bash
pytest
```
The included tests cover the health-check endpoint and verify that the `/chat` route correctly forwards messages to the RAG provider.

## Project structure
```
.
├── data/                # Source documentation used to build the vector store
├── db_metadata_v5/      # Persisted Chroma database files
├── main.py              # FastAPI application entry point
├── models/              # Pydantic models shared across the API
├── providers/           # Integration with the Ollama-based RAG provider
├── public/              # Static assets served by the API
├── scripts/             # Utilities for scraping and ingesting documentation into Chroma
└── tests/               # Pytest suite exercising the API
```

## Development tips
- The Ollama-backed RAG provider is loaded lazily.  If the required LangChain modules are not installed, automated tests can still run by mocking the provider.
- Use `scripts/ingest.py` to rebuild the vector store whenever new documentation is added to `data/`.
