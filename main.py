"""Telegram bot entry point for the Retrieval-Augmented Generation assistant."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from typing import Optional

from telegram import Update
from telegram.constants import ChatAction, MessageLimit
from telegram.error import TelegramError
try:  # pragma: no cover - depends on telegram package version
    from telegram.helpers import ChatActionSender  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - depends on telegram package version
    ChatActionSender = None  # type: ignore[assignment]
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

OLLAMA_TIMEOUT_ENV = "OLLAMA_TIMEOUT"


def _get_ollama_timeout() -> Optional[float]:
    """Return the configured timeout for Ollama requests, if any."""

    raw_value = os.getenv(OLLAMA_TIMEOUT_ENV)
    if not raw_value:
        return None
    try:
        timeout = float(raw_value)
    except ValueError:
        LOGGER.warning("Invalid OLLAMA_TIMEOUT '%s'; ignoring.", raw_value)
        return None
    if timeout <= 0:
        LOGGER.warning("OLLAMA_TIMEOUT must be positive; ignoring '%s'.", raw_value)
        return None
    return timeout


async def _query_rag_with_timeout(message: ChatMessage, session_id: str) -> str:
    """Run the blocking RAG query off the event loop honoring the configured timeout."""

    timeout = _get_ollama_timeout()
    coroutine = asyncio.to_thread(ollama.query_rag, message, session_id)
    if timeout is not None:
        return await asyncio.wait_for(coroutine, timeout=timeout)
    return await coroutine


def chunk_response(text: str, limit: int = int(MessageLimit.MAX_TEXT_LENGTH)) -> list[str]:
    """Split *text* into Telegram-sized chunks while respecting Markdown code blocks."""

    if not text:
        return []

    def last_safe_break(segment: str) -> int:
        inside_code = False
        last_break = -1
        idx = 0
        while idx < len(segment):
            if segment.startswith("```", idx):
                inside_code = not inside_code
                idx += 3
                continue
            if segment[idx] == "\n" and not inside_code:
                last_break = idx
            idx += 1
        return last_break

    chunks: list[str] = []
    position = 0
    text_length = len(text)
    while position < text_length:
        end = min(position + limit, text_length)
        segment = text[position:end]
        if end < text_length:
            split_index = last_safe_break(segment)
            if split_index != -1:
                split_index += 1  # include the newline at the break point
            else:
                split_index = len(segment)
        else:
            split_index = len(segment)

        if split_index == 0:
            split_index = len(segment)

        chunk = segment[:split_index]
        chunks.append(chunk)
        position += split_index

    return chunks


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

    chat_id = update.effective_chat.id if update.effective_chat else None

    def _truncate(value: Optional[str], limit: int = 200) -> str:
        if value is None:
            return ""
        if len(value) <= limit:
            return value
        return value[: limit - 1] + "\u2026"

    LOGGER.info("Received message in chat %s: %s", chat_id, _truncate(text))

    session_id = str(chat_id) if chat_id is not None else ""
    message_payload = ChatMessage(question=text)

    try:
        if chat_id is not None and ChatActionSender is not None:
            async with ChatActionSender(
                action=ChatAction.TYPING, chat_id=chat_id, bot=context.bot
            ):
                response_text = await _query_rag_with_timeout(message_payload, session_id)
        else:
            if chat_id is not None:
                await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            response_text = await _query_rag_with_timeout(message_payload, session_id)
        LOGGER.info("Assistant response for chat %s: %s", chat_id, _truncate(response_text))
    except asyncio.TimeoutError:
        LOGGER.warning("Timed out querying RAG backend for chat %s", chat_id)
        await update.message.reply_text(
            "Sorry, the request timed out before I could reply. Please try again later."
        )
        return
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to query RAG backend for chat %s", chat_id)
        await update.message.reply_text(
            "Sorry, something went wrong while processing your request. Please try again later."
        )
        return

    try:
        chunks = chunk_response(response_text)
        for chunk in chunks:
            await update.message.reply_text(chunk)
    except TelegramError:
        LOGGER.exception("Failed to send response to chat %s", chat_id)
        apology = "Sorry, I couldn't deliver the response due to a Telegram error. Please try again later."
        if chat_id is not None:
            try:
                await context.bot.send_message(chat_id=chat_id, text=apology)
            except TelegramError:
                LOGGER.exception("Failed to send failure notice to chat %s", chat_id)
        return


def build_application(token: str) -> Application:
    """Construct the Telegram application with the configured handlers."""

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    """Run the Telegram bot backed by the Ollama RAG pipeline."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

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
