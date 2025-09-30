"""Tests for the Telegram bot entry point."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.append(str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402  - imported after adjusting sys.path


def test_handle_text_triggers_typing_indicator(monkeypatch):
    """Ensure the chat action helper is used while querying the backend."""

    calls = []

    class DummySender:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(main, "ChatActionSender", DummySender)
    monkeypatch.setattr(main.ollama, "query_rag", lambda message, chat_id: "response")

    message = SimpleNamespace(text="hello", reply_text=AsyncMock())
    update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=42))
    context = SimpleNamespace(bot=object())

    asyncio.run(main.handle_text(update, context))

    assert calls == [
        ((), {"action": main.ChatAction.TYPING, "chat_id": 42, "bot": context.bot})
    ]
    message.reply_text.assert_awaited_once_with("response")


def test_handle_text_timeout_sends_notice_and_recovers(monkeypatch):
    """The bot should notify the user on timeout and continue serving new messages."""

    monkeypatch.setenv(main.OLLAMA_TIMEOUT_ENV, "0.01")
    monkeypatch.setattr(main, "ChatActionSender", None)

    async def slow_action(func, *args, **kwargs):
        try:
            await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            raise
        return func(*args, **kwargs)

    async def fast_action(func, *args, **kwargs):
        return func(*args, **kwargs)

    actions = [slow_action, fast_action]

    async def fake_to_thread(func, *args, **kwargs):
        if actions:
            action = actions.pop(0)
        else:  # pragma: no cover - defensive fallback
            action = fast_action
        return await action(func, *args, **kwargs)

    monkeypatch.setattr(main.asyncio, "to_thread", fake_to_thread)

    query_calls = []

    def fake_query(message, session_id):
        query_calls.append((message.question, session_id))
        return "resolved response"

    monkeypatch.setattr(main.ollama, "query_rag", fake_query)

    first_message = SimpleNamespace(text="first", reply_text=AsyncMock())
    second_message = SimpleNamespace(text="second", reply_text=AsyncMock())

    chat = SimpleNamespace(id=7)
    bot = SimpleNamespace(send_chat_action=AsyncMock())
    context = SimpleNamespace(bot=bot)

    asyncio.run(main.handle_text(SimpleNamespace(message=first_message, effective_chat=chat), context))
    asyncio.run(main.handle_text(SimpleNamespace(message=second_message, effective_chat=chat), context))

    first_message.reply_text.assert_awaited_once_with(
        "Sorry, the request timed out before I could reply. Please try again later."
    )
    second_message.reply_text.assert_awaited_once_with("resolved response")
    assert bot.send_chat_action.await_count == 2
    assert query_calls == [("second", "7")]
