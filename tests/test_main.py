import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

import main
from models.index import ChatMessage


def test_read_root():
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"Hello": "world"}


def test_chat_endpoint(monkeypatch):
    client = TestClient(main.app)
    captured = {}

    def fake_query(message: ChatMessage, session_id: str) -> str:
        captured["message"] = message
        captured["session_id"] = session_id
        return "mocked response"

    monkeypatch.setattr(main, "query_rag", fake_query)

    response = client.post("/chat/test-session", json={"question": "Hello"})

    assert response.status_code == 200
    assert response.json() == {"response": "mocked response"}
    assert isinstance(captured["message"], ChatMessage)
    assert captured["message"].question == "Hello"
    assert captured["session_id"] == "test-session"
