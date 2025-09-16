"""Telegram bot entry point for the Retrieval-Augmented Generation assistant."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from models.index import ChatMessage
from providers import ollama

LOGGER = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greet the user when they issue the /start command."""

    if update.message is None:
        return

    user_first_name: Optional[str] = None
    if update.effective_user is not None:
        user_first_name = update.effective_user.first_name

    greeting = "Hello!"
    if user_first_name:
        greeting = f"Hello, {user_first_name}!"

    await update.message.reply_text(
        f"{greeting} I'm your RAG assistant. Ask me a question and I'll search the knowledge base for you."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages by querying the RAG pipeline."""

    if update.message is None:
        return

    text = update.message.text
    if not text:
        return

    chat_id = str(update.effective_chat.id) if update.effective_chat else ""

    try:
        response_text = ollama.query_rag(ChatMessage(question=text), chat_id)
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to query RAG backend for chat %s", chat_id)
        await update.message.reply_text(
            "Sorry, something went wrong while processing your request. Please try again later."
        )
        return

    await update.message.reply_text(response_text)


def build_application(token: str) -> Application:
    """Construct the Telegram application with the configured handlers."""

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    """Run the Telegram bot backed by the Ollama RAG pipeline."""

    logging.basicConfig(level=logging.INFO)

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError(
            "Environment variable TELEGRAM_TOKEN must be set to start the Telegram bot."
        )

    try:
        ollama_process = subprocess.Popen(["ollama", "serve"])
    except OSError as exc:  # pragma: no cover - depends on host environment
        raise RuntimeError("Failed to start the Ollama backend using 'ollama serve'.") from exc

    application = build_application(token)

    try:
        application.run_polling()
    finally:
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            LOGGER.warning("Ollama backend did not terminate gracefully; killing it.")
            ollama_process.kill()
            ollama_process.wait()


if __name__ == "__main__":  # pragma: no cover - runtime entry point
    main()
