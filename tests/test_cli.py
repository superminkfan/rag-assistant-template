from pathlib import Path
import io
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

    args = parser.parse_args(
        [
            "ingest",
            "--source-type",
            "confluence-snapshot",
            "--source-id",
            "sberworks",
            "--replace-source-id",
        ]
    )
    assert args.source_id == "sberworks"
    assert args.replace_source_id is True

    args = parser.parse_args(["ask", "what", "happened"])
    assert args.command == "ask"
    assert args.question == ["what", "happened"]

    args = parser.parse_args(["analyze-incident", "/tmp/incident.txt"])
    assert args.command == "analyze-incident"
    assert args.path == Path("/tmp/incident.txt")

    args = parser.parse_args(["inspect-index", "--sample-limit", "5"])
    assert args.command == "inspect-index"
    assert args.sample_limit == 5

    args = parser.parse_args(["evaluate-retrieval", "--limit", "3"])
    assert args.command == "evaluate-retrieval"
    assert args.limit == 3

    args = parser.parse_args(
        ["inspect-source", "--source", "/tmp/docs", "--source-type", "ignite-docs"]
    )
    assert args.command == "inspect-source"
    assert args.source == Path("/tmp/docs")
    assert args.source_type == "ignite-docs"

    args = parser.parse_args(
        ["inspect-source", "--source-type", "ignite-firefighter-tree"]
    )
    assert args.source_type == "ignite-firefighter-tree"

    args = parser.parse_args(
        [
            "snapshot-confluence",
            "--source-id",
            "sberworks",
            "--offline-dir",
            "/tmp/html",
        ]
    )
    assert args.offline_dir == Path("/tmp/html")


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
    assert calls["replace_source_id"] is False
    assert "Ingested 2 documents into 5 chunks" in capsys.readouterr().out


def test_cli_snapshots_offline_confluence(tmp_path, monkeypatch, capsys):
    config_path = write_config(
        tmp_path,
        """
confluence:
  output_root: snapshots
""",
    )
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    pages = [{"page_content": "content", "metadata": {"source_id": "sberworks"}}]
    calls = {}

    def fake_collect(path, *, source_id):
        calls["collect"] = (path, source_id)
        return pages

    def fake_write(**kwargs):
        calls["write"] = kwargs
        return tmp_path / "published"

    monkeypatch.setattr(cli, "collect_offline_pages", fake_collect)
    monkeypatch.setattr(cli, "write_confluence_snapshot", fake_write)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "snapshot-confluence",
            "--source-id",
            "sberworks",
            "--offline-dir",
            str(html_dir),
        ]
    )

    assert result == 0
    assert calls["collect"] == (html_dir, "sberworks")
    assert calls["write"]["output_root"] == (tmp_path / "snapshots").resolve()
    assert calls["write"]["mode"] == "offline-html"
    assert "with 1 pages" in capsys.readouterr().out


def test_cli_resolves_configured_confluence_snapshot(tmp_path, monkeypatch):
    config_path = write_config(
        tmp_path,
        """
confluence:
  output_root: snapshots
""",
    )
    calls = {}
    monkeypatch.setattr(cli, "build_local_vector_store", lambda **kwargs: object())

    def fake_ingest(source_path, **kwargs):
        calls["source_path"] = source_path
        return {"documents": 0, "chunks": 0, "db_path": "db"}

    monkeypatch.setattr(cli, "ingest_source", fake_ingest)

    result = cli.main(
        [
            "--config",
            str(config_path),
            "ingest",
            "--source-type",
            "confluence-snapshot",
            "--source-id",
            "sberworks",
        ]
    )

    assert result == 0
    assert calls["source_path"] == (tmp_path / "snapshots/sberworks/latest").resolve()


def test_cli_evaluates_retrieval_without_generation(tmp_path, monkeypatch, capsys):
    config_path = write_config(tmp_path)
    cases_path = tmp_path / "cases.json"
    cases_path.write_text("[]", encoding="utf-8")
    retriever = object()
    monkeypatch.setattr(
        cli,
        "build_local_rag",
        lambda **kwargs: SimpleNamespace(retriever=retriever),
    )
    monkeypatch.setattr(cli, "load_evaluation_cases", lambda path: [{"id": "one"}])
    monkeypatch.setattr(
        cli,
        "evaluate_retrieval",
        lambda cases, *, retriever, limit: {"cases": 1},
    )
    monkeypatch.setattr(cli, "format_evaluation_summary", lambda summary: "Cases: 1")

    result = cli.main(
        [
            "--config",
            str(config_path),
            "evaluate-retrieval",
            "--cases",
            str(cases_path),
        ]
    )

    assert result == 0
    assert capsys.readouterr().out.strip() == "Cases: 1"


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
    monkeypatch.setattr(cli.time, "perf_counter", iter([10.0, 12.5]).__next__)

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
    assert capsys.readouterr().out.strip() == "analysis\n\nResponse time: 2.50 s"


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
    monkeypatch.setattr(cli.time, "perf_counter", iter([10.0, 10.75]).__next__)

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
    assert capsys.readouterr().out.strip() == "answer\n\nResponse time: 0.75 s"


def test_run_with_spinner_animates_and_clears_interactive_terminal():
    class TtyBuffer(io.StringIO):
        def isatty(self):
            return True

    output = TtyBuffer()

    result, elapsed = cli.run_with_spinner(lambda: "answer", stream=output)

    assert result == "answer"
    assert elapsed >= 0
    assert "Assistant is thinking" in output.getvalue()
    assert output.getvalue().endswith("\r")


def test_run_with_spinner_stays_silent_for_redirected_output():
    output = io.StringIO()

    result, _ = cli.run_with_spinner(lambda: "answer", stream=output)

    assert result == "answer"
    assert output.getvalue() == ""


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
