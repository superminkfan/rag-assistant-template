import os
from typing import List

from fastapi.middleware.cors import CORSMiddleware

from models.index import ChatMessage
from providers.ollama import query_rag

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def _load_allowed_origins() -> List[str]:
    """Return a list of allowed CORS origins.

    Origins can be supplied via the ``ALLOWED_ORIGINS`` environment variable
    as a comma separated list. When the variable is not provided, fall back to
    a set of local development domains.
    """

    env_value = os.getenv("ALLOWED_ORIGINS")
    if env_value:
        return [origin.strip() for origin in env_value.split(",") if origin.strip()]

    return [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
    ]


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
async def read_root():
    return {"Hello": "world"}


@app.post("/chat/{chat_id}")
async def ask(chat_id: str, message: ChatMessage):
    return {"response": query_rag(message, chat_id)}