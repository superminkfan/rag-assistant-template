"""YAML-backed runtime configuration for local commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_assistant.settings import (
    DEFAULT_ARTIFACTS_ROOT,
    DEFAULT_CONFIG_PATHS,
    DEFAULT_DB_PATH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_FINAL_K,
    DEFAULT_JIRA_OUTPUT_ROOT,
    DEFAULT_KEYWORD_K,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_VECTOR_K,
)


@dataclass(frozen=True)
class PathsConfig:
    datagrid_docs: Path | None
    ignite_docs: Path | None
    db_path: Path
    artifacts_root: Path


@dataclass(frozen=True)
class JiraConfig:
    base_url: str | None
    jql: str | None
    cert_path: Path | None
    output_root: Path


@dataclass(frozen=True)
class OllamaConfig:
    model: str
    embedding_model: str
    temperature: float


@dataclass(frozen=True)
class RetrievalConfig:
    vector_k: int
    keyword_k: int
    final_k: int


@dataclass(frozen=True)
class AppConfig:
    config_path: Path | None
    paths: PathsConfig
    jira: JiraConfig
    ollama: OllamaConfig
    retrieval: RetrievalConfig


def load_config(path: Path | None = None) -> AppConfig:
    """Load runtime config from YAML, falling back to safe local defaults."""

    config_path = _find_config_path(path)
    raw = _read_yaml(config_path) if config_path else {}
    base_dir = config_path.parent if config_path else Path.cwd()

    paths_raw = _section(raw, "paths")
    artifacts_root = _path_value(
        paths_raw.get("artifacts_root"),
        base_dir=base_dir,
        default=DEFAULT_ARTIFACTS_ROOT,
    )
    db_path = _path_value(
        paths_raw.get("db_path"),
        base_dir=base_dir,
        default=artifacts_root / "chroma"
        if artifacts_root != DEFAULT_ARTIFACTS_ROOT
        else DEFAULT_DB_PATH,
    )
    paths = PathsConfig(
        datagrid_docs=_optional_path(paths_raw.get("datagrid_docs"), base_dir=base_dir),
        ignite_docs=_optional_path(paths_raw.get("ignite_docs"), base_dir=base_dir),
        db_path=db_path,
        artifacts_root=artifacts_root,
    )

    jira_raw = _section(raw, "jira")
    jira = JiraConfig(
        base_url=_optional_str(jira_raw.get("base_url")),
        jql=_optional_str(jira_raw.get("jql")),
        cert_path=_optional_path(jira_raw.get("cert_path"), base_dir=base_dir),
        output_root=_path_value(
            jira_raw.get("output_root"),
            base_dir=base_dir,
            default=artifacts_root / "jira" / "export"
            if artifacts_root != DEFAULT_ARTIFACTS_ROOT
            else DEFAULT_JIRA_OUTPUT_ROOT,
        ),
    )

    ollama_raw = _section(raw, "ollama")
    ollama = OllamaConfig(
        model=str(ollama_raw.get("model") or DEFAULT_OLLAMA_MODEL),
        embedding_model=str(
            ollama_raw.get("embedding_model") or DEFAULT_EMBEDDING_MODEL
        ),
        temperature=float(ollama_raw.get("temperature", DEFAULT_TEMPERATURE)),
    )

    retrieval_raw = _section(raw, "retrieval")
    retrieval = RetrievalConfig(
        vector_k=int(retrieval_raw.get("vector_k", DEFAULT_VECTOR_K)),
        keyword_k=int(retrieval_raw.get("keyword_k", DEFAULT_KEYWORD_K)),
        final_k=int(retrieval_raw.get("final_k", DEFAULT_FINAL_K)),
    )

    return AppConfig(
        config_path=config_path,
        paths=paths,
        jira=jira,
        ollama=ollama,
        retrieval=retrieval,
    )


def source_path_for_type(config: AppConfig, source_type: str) -> Path | None:
    """Return configured source path for a supported source type."""

    if source_type == "datagrid-docs":
        return config.paths.datagrid_docs
    if source_type == "ignite-docs":
        return config.paths.ignite_docs
    if source_type == "jira-snapshot":
        return config.jira.output_root / "latest" / "curated"
    return None


def _find_config_path(path: Path | None) -> Path | None:
    if path is not None:
        resolved = path.expanduser()
        if not resolved.is_file():
            raise FileNotFoundError(f"Config file not found: {resolved}")
        return resolved.resolve()

    for candidate in DEFAULT_CONFIG_PATHS:
        expanded = candidate.expanduser()
        if expanded.is_file():
            return expanded.resolve()
    return None


def _read_yaml(path: Path) -> dict[str, Any]:
    import yaml

    with path.open(encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data


def _section(raw: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw.get(name) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section must be a mapping: {name}")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_path(value: Any, *, base_dir: Path) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _normalize_path(Path(text), base_dir=base_dir)


def _path_value(value: Any, *, base_dir: Path, default: Path) -> Path:
    optional = _optional_path(value, base_dir=base_dir)
    return optional if optional is not None else default.expanduser()


def _normalize_path(path: Path, *, base_dir: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return (base_dir / expanded).resolve()
