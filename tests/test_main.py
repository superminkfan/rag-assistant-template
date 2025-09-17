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
