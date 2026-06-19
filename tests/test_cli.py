from pathlib import Path
from types import SimpleNamespace

from rag_assistant import cli
from rag_assistant.settings import DEFAULT_VECTOR_K


def write_config(tmp_path, text="{}"):
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_build_parser_supports_cli_commands():
    parser = cli.build_parser()

    args = parser.parse_args(
        [
            "ingest",
            "--source",
            "/tmp/snapshot",
            "--source-type",
            "jira-snapshot",
            "--limit",
            "3",
            "--reset",
        ]
    )
    assert args.command == "ingest"
    assert args.source == Path("/tmp/snapshot")
    assert args.source_type == "jira-snapshot"
    assert args.limit == 3
    assert args.reset is True

    args = parser.parse_args(
        [
            "ingest",
            "--source",
            "/tmp/snapshot",
            "--source-type",
            "jira-snapshot",
            "--replace-source-type",
        ]
    )
    assert args.replace_source_type is True

    args = parser.parse_args(["ask", "what", "happened"])
    assert args.command == "ask"
    assert args.question == ["what", "happened"]

    args = parser.parse_args(["analyze-incident", "/tmp/incident.txt"])
    assert args.command == "analyze-incident"
    assert args.path == Path("/tmp/incident.txt")

    args = parser.parse_args(["inspect-index", "--sample-limit", "5"])
    assert args.command == "inspect-index"
    assert args.sample_limit == 5

    args = parser.parse_args(
        ["inspect-source", "--source", "/tmp/docs", "--source-type", "ignite-docs"]
    )
    assert args.command == "inspect-source"
    assert args.source == Path("/tmp/docs")
    assert args.source_type == "ignite-docs"


def test_cli_ingest_dispatches(monkeypatch, tmp_path, capsys):
    config_path = write_config(tmp_path)
    calls = {}
    vector_store = object()

    def fake_build_vector_store(**kwargs):
        calls["factory"] = kwargs
        return vector_store

    def fake_ingest(source_path, **kwargs):
        calls["source_path"] = source_path
        calls.update(kwargs)
        return {"documents": 2, "chunks": 5, "db_path": "db"}

    monkeypatch.setattr(cli, "build_local_vector_store", fake_build_vector_store)
    monkeypatch.setattr(cli, "ingest_source", fake_ingest)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "--db-path",
            str(tmp_path / "db"),
            "ingest",
            "--source",
            str(tmp_path),
        ]
    )

    assert result == 0
    assert calls["source_path"] == tmp_path
    assert calls["factory"] == {
        "db_path": tmp_path / "db",
        "embedding_model": "mxbai-embed-large",
        "reset": False,
    }
    assert calls["vector_store"] is vector_store
    assert calls["replace_source_type"] is False
    assert "Ingested 2 documents into 5 chunks" in capsys.readouterr().out


def test_cli_ingest_uses_configured_source(monkeypatch, tmp_path):
    docs_path = tmp_path / "datagrid-docs"
    config_path = write_config(
        tmp_path,
        f"""
paths:
  datagrid_docs: {docs_path}
""",
    )
    calls = {}

    monkeypatch.setattr(cli, "build_local_vector_store", lambda **kwargs: object())
    def fake_ingest(source_path, **kwargs):
        calls["source_path"] = source_path
        return {"documents": 0, "chunks": 0, "db_path": "db"}

    monkeypatch.setattr(cli, "ingest_source", fake_ingest)

    result = cli.main(["--config", str(config_path), "ingest"])

    assert result == 0
    assert calls["source_path"] == docs_path


def test_cli_analyze_incident_dispatches(monkeypatch, tmp_path, capsys):
    config_path = write_config(tmp_path)
    incident = tmp_path / "incident.txt"
    incident.write_text("WAL archive grows quickly", encoding="utf-8")
    calls = {}
    llm = object()
    retriever = object()

    def fake_build_local_rag(**kwargs):
        calls["factory"] = kwargs
        return SimpleNamespace(llm=llm, retriever=retriever)

    def fake_analyze_incident(text, **kwargs):
        calls["text"] = text
        calls.update(kwargs)
        return "analysis"

    monkeypatch.setattr(cli, "build_local_rag", fake_build_local_rag)
    monkeypatch.setattr(cli, "analyze_incident", fake_analyze_incident)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "--db-path",
            str(tmp_path / "db"),
            "analyze-incident",
            str(incident),
        ]
    )

    assert result == 0
    assert calls["text"] == "WAL archive grows quickly"
    assert calls["factory"]["db_path"] == tmp_path / "db"
    assert calls["factory"]["model"] == "llama3.2:latest"
    assert calls["factory"]["embedding_model"] == "mxbai-embed-large"
    assert calls["llm"] is llm
    assert calls["retriever"] is retriever
    assert capsys.readouterr().out.strip() == "analysis"


def test_cli_ask_dispatches_with_built_components(monkeypatch, tmp_path, capsys):
    config_path = write_config(tmp_path)
    calls = {}
    llm = object()
    retriever = object()

    def fake_build_local_rag(**kwargs):
        calls["factory"] = kwargs
        return SimpleNamespace(llm=llm, retriever=retriever)

    def fake_ask(question, **kwargs):
        calls["question"] = question
        calls.update(kwargs)
        return "answer"

    monkeypatch.setattr(cli, "build_local_rag", fake_build_local_rag)
    monkeypatch.setattr(cli, "ask", fake_ask)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "--db-path",
            str(tmp_path / "db"),
            "ask",
            "what",
            "happened",
        ]
    )

    assert result == 0
    assert calls["factory"]["db_path"] == tmp_path / "db"
    assert calls["factory"]["vector_k"] == DEFAULT_VECTOR_K
    assert calls["question"] == "what happened"
    assert calls["llm"] is llm
    assert calls["retriever"] is retriever
    assert capsys.readouterr().out.strip() == "answer"


def test_cli_inspect_index_dispatches(monkeypatch, tmp_path, capsys):
    config_path = write_config(tmp_path)
    calls = {}

    def fake_inspect_index(db_path, **kwargs):
        calls["db_path"] = db_path
        calls.update(kwargs)
        return {"db_path": str(db_path), "collections": []}

    monkeypatch.setattr(cli, "inspect_index", fake_inspect_index)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "--db-path",
            str(tmp_path / "db"),
            "inspect-index",
            "--sample-limit",
            "7",
        ]
    )

    assert result == 0
    assert calls["db_path"] == tmp_path / "db"
    assert calls["sample_limit"] == 7
    assert "No collections found" in capsys.readouterr().out


def test_cli_inspect_source_dispatches(monkeypatch, tmp_path, capsys):
    config_path = write_config(tmp_path)
    calls = {}

    def fake_inspect_source(source_path, **kwargs):
        calls["source_path"] = source_path
        calls.update(kwargs)
        return {
            "source_path": str(source_path),
            "source_type": kwargs["source_type"],
            "documents": 1,
            "chunks": 2,
            "unique_chunk_ids": 2,
            "component": {"persistence": 2},
            "guide": {"persistence": 2},
        }

    monkeypatch.setattr(cli, "inspect_source", fake_inspect_source)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "inspect-source",
            "--source",
            str(tmp_path),
            "--source-type",
            "ignite-docs",
            "--limit",
            "3",
        ]
    )

    assert result == 0
    assert calls["source_path"] == tmp_path
    assert calls["source_type"] == "ignite-docs"
    assert calls["limit"] == 3
    assert "Documents: 1" in capsys.readouterr().out
