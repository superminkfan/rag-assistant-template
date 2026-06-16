from pathlib import Path

import pytest

from rag_assistant import config as config_module
from rag_assistant.config import load_config, source_path_for_type
from rag_assistant.settings import DEFAULT_DB_PATH, DEFAULT_JIRA_OUTPUT_ROOT


def test_load_config_reads_yaml_sections(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
paths:
  datagrid_docs: docs/datagrid
  ignite_docs: ~/ignite-docs
  db_path: artifacts/chroma
  artifacts_root: artifacts
jira:
  base_url: https://jira.example
  jql: project = TEST
  cert_path: certs/client.pem
ollama:
  model: llama-test
  embedding_model: embed-test
  temperature: 0.2
retrieval:
  vector_k: 11
  keyword_k: 12
  final_k: 13
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.config_path == config_path.resolve()
    assert config.paths.datagrid_docs == (tmp_path / "docs/datagrid").resolve()
    assert config.paths.ignite_docs == Path.home() / "ignite-docs"
    assert config.paths.db_path == (tmp_path / "artifacts/chroma").resolve()
    assert config.paths.artifacts_root == (tmp_path / "artifacts").resolve()
    assert config.jira.base_url == "https://jira.example"
    assert config.jira.jql == "project = TEST"
    assert config.jira.cert_path == (tmp_path / "certs/client.pem").resolve()
    assert config.jira.output_root == (tmp_path / "artifacts/jira/export").resolve()
    assert config.ollama.model == "llama-test"
    assert config.ollama.embedding_model == "embed-test"
    assert config.ollama.temperature == 0.2
    assert config.retrieval.vector_k == 11
    assert config.retrieval.keyword_k == 12
    assert config.retrieval.final_k == 13


def test_load_config_uses_safe_defaults_without_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        config_module,
        "DEFAULT_CONFIG_PATHS",
        (tmp_path / "missing-local.yaml", tmp_path / "missing-home.yaml"),
    )

    config = load_config()

    assert config.config_path is None
    assert config.paths.db_path == DEFAULT_DB_PATH
    assert config.jira.output_root == DEFAULT_JIRA_OUTPUT_ROOT


def test_load_config_raises_for_missing_explicit_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(tmp_path / "missing.yaml")


def test_source_path_for_type_uses_configured_paths(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
paths:
  datagrid_docs: datagrid
  artifacts_root: artifacts
jira:
  output_root: jira-out
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert source_path_for_type(config, "datagrid-docs") == (tmp_path / "datagrid").resolve()
    assert source_path_for_type(config, "ignite-docs") is None
    assert source_path_for_type(config, "jira-snapshot") == (
        tmp_path / "jira-out/latest/curated"
    ).resolve()
