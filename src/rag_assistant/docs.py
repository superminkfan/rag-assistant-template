"""Documentation loading and metadata extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import re
import sys
from typing import Any, Iterable


@dataclass(frozen=True)
class SourceDocument:
    """A normalized source document before vector-store chunking."""

    page_content: str
    metadata: dict[str, Any]


def load_markdown_source(
    source_path: Path,
    *,
    source_type: str = "datagrid-docs",
) -> list[SourceDocument]:
    """Load Markdown documentation from a datagrid-docs style repository."""

    source_root = source_path.resolve()
    documentation_root = source_root / "documentation"
    documents_root = documentation_root / "documents"
    if not documents_root.exists():
        documents_root = source_root

    manifest = read_doc_manifest(documentation_root / "doc.yaml")
    substitutions = manifest.get("substitutions", {})

    documents: list[SourceDocument] = []
    for markdown_path in sorted(documents_root.rglob("*.md")):
        raw_text = _read_text(markdown_path)
        text = normalize_markdown(raw_text, substitutions=substitutions)
        title = extract_first_heading(text) or markdown_path.stem.replace("-", " ")

        source_rel_path = markdown_path.relative_to(source_root).as_posix()
        docs_rel_path = markdown_path.relative_to(documents_root).as_posix()
        guide = docs_rel_path.split("/", 1)[0]

        metadata = {
            "source": source_rel_path,
            "source_path": source_rel_path,
            "source_type": source_type,
            "source_format": "markdown",
            "doc_set_code": str(manifest.get("code") or ""),
            "product": "DataGrid" if source_type == "datagrid-docs" else "Ignite",
            "product_version": str(manifest.get("version") or ""),
            "release_id": str(manifest.get("sberproject_release_id") or ""),
            "archive_group_id": str(manifest.get("archive_group_id") or ""),
            "guide": guide,
            "component": infer_component(guide, markdown_path.stem, title),
            "title": title,
        }
        documents.append(SourceDocument(page_content=text, metadata=metadata))

    return documents


def load_asciidoc_source(
    source_path: Path,
    *,
    source_type: str = "ignite-docs",
) -> list[SourceDocument]:
    """Load AsciiDoc documentation from the existing Ignite docs corpus."""

    source_root = source_path.resolve()
    documents: list[SourceDocument] = []

    for adoc_path in sorted(source_root.rglob("*.adoc")):
        raw_text = _read_text(adoc_path)
        text = normalize_asciidoc(raw_text)
        title = extract_first_asciidoc_heading(text) or adoc_path.stem.replace("-", " ")

        source_rel_path = adoc_path.relative_to(source_root).as_posix()
        guide = source_rel_path.split("/", 1)[0] if "/" in source_rel_path else "root"

        metadata = {
            "source": source_rel_path,
            "source_path": source_rel_path,
            "source_type": source_type,
            "source_format": "asciidoc",
            "doc_set_code": "IGNITE",
            "product": "Ignite",
            "product_version": "",
            "release_id": "",
            "archive_group_id": "",
            "guide": guide,
            "component": infer_component(guide, adoc_path.stem, title),
            "title": title,
        }
        documents.append(SourceDocument(page_content=text, metadata=metadata))

    return documents


def load_source_documents(source_path: Path, *, source_type: str) -> list[SourceDocument]:
    """Dispatch to the loader that matches the requested source type."""

    if source_type == "datagrid-docs":
        return load_markdown_source(source_path, source_type=source_type)
    if source_type == "ignite-docs":
        return load_asciidoc_source(source_path, source_type=source_type)
    if source_type == "jira-snapshot":
        return load_jira_snapshot_source(source_path, source_type=source_type)
    raise ValueError(f"Unsupported source_type: {source_type}")


def load_jira_snapshot_source(
    source_path: Path,
    *,
    source_type: str = "jira-snapshot",
) -> list[SourceDocument]:
    """Load validated issue and comment tables from a Jira snapshot variant."""

    source_root = source_path.resolve()
    issues_path = source_root / "issues.csv"
    comments_path = source_root / "comments.csv"
    if not issues_path.is_file() or not comments_path.is_file():
        raise FileNotFoundError(
            f"Jira snapshot requires issues.csv and comments.csv in {source_root}"
        )

    _raise_csv_field_limit()
    issue_rows = _read_csv_rows(
        issues_path,
        required_fields={
            "schema_version",
            "issue_key",
            "support_key",
            "summary",
            "description",
            "comment_count",
            "substantive_comment_count",
            "curated_eligible",
            "quality_flags_json",
        },
    )
    comment_rows = _read_csv_rows(
        comments_path,
        required_fields={
            "schema_version",
            "issue_key",
            "support_key",
            "comment_id",
            "sequence",
            "author",
            "created_at",
            "body",
            "is_substantive",
        },
    )
    _validate_jira_snapshot_rows(issue_rows, comment_rows)

    variant = source_root.name
    documents: list[SourceDocument] = []
    issues_by_key = {row["issue_key"]: row for row in issue_rows}

    for row in issue_rows:
        issue_key = row["issue_key"]
        support_key = row.get("support_key", "")
        title = row.get("summary", "") or issue_key
        description = row.get("description", "") or "No description provided."
        components = _json_string_list(row.get("components_json", "[]"))
        quality_flags = _json_string_list(row.get("quality_flags_json", "[]"))
        source = f"jira://issue/{issue_key}"
        component = infer_component(
            "jira",
            " ".join(components),
            f"{title} {description[:1000]}",
        )
        metadata = _jira_snapshot_base_metadata(
            row,
            source=source,
            source_type=source_type,
            variant=variant,
            title=title,
            component=component,
            quality_flags=quality_flags,
        )
        metadata.update(
            {
                "record_type": "issue",
                "section": "Client request",
                "author": "",
                "comment_id": "",
                "comment_sequence": "",
                "is_substantive": "",
            }
        )
        documents.append(SourceDocument(page_content=description, metadata=metadata))

    for row in comment_rows:
        issue = issues_by_key[row["issue_key"]]
        issue_key = row["issue_key"]
        title = issue.get("summary", "") or issue_key
        body = row.get("body", "") or "No comment text provided."
        components = _json_string_list(issue.get("components_json", "[]"))
        quality_flags = _json_string_list(issue.get("quality_flags_json", "[]"))
        comment_id = row["comment_id"]
        source = f"jira://issue/{issue_key}/comment/{comment_id}"
        component = infer_component(
            "jira",
            " ".join(components),
            f"{title} {body[:1000]}",
        )
        metadata = _jira_snapshot_base_metadata(
            issue,
            source=source,
            source_type=source_type,
            variant=variant,
            title=title,
            component=component,
            quality_flags=quality_flags,
        )
        metadata.update(
            {
                "record_type": "comment",
                "section": f"Comment {row.get('sequence') or ''}".strip(),
                "author": row.get("author", ""),
                "comment_id": comment_id,
                "comment_sequence": row.get("sequence", ""),
                "comment_created_at": row.get("created_at", ""),
                "comment_updated_at": row.get("updated_at", ""),
                "is_substantive": row.get("is_substantive", ""),
            }
        )
        documents.append(SourceDocument(page_content=body, metadata=metadata))

    return documents


def read_doc_manifest(path: Path) -> dict[str, Any]:
    """Read the simple doc.yaml shape used by datagrid-docs without requiring PyYAML."""

    if not path.exists():
        return {}

    result: dict[str, Any] = {}
    current_mapping: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0 and line.endswith(":"):
            current_mapping = line[:-1].strip()
            result[current_mapping] = {}
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = _clean_yaml_scalar(value)

        if indent > 0 and current_mapping:
            nested = result.setdefault(current_mapping, {})
            if isinstance(nested, dict):
                nested[key] = value
        else:
            current_mapping = None
            result[key] = value

    return result


def normalize_markdown(text: str, *, substitutions: dict[str, Any] | None = None) -> str:
    """Normalize MyST-ish Markdown into text that chunks well for RAG."""

    normalized = text
    for key, value in (substitutions or {}).items():
        replacement = str(value)
        normalized = normalized.replace("{{" + key + "}}", replacement)
        normalized = normalized.replace("{" + key + "}", replacement)

    lines: list[str] = []
    for raw_line in normalized.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        directive = re.match(r"^:{3,}\{([^}]+)\}\s*(.*)$", stripped)
        if directive:
            name = directive.group(1).strip()
            value = directive.group(2).strip()
            replacement = _directive_to_text(name, value)
            if replacement:
                lines.append(replacement)
            continue

        if re.match(r"^:{3,}$", stripped):
            continue

        if re.match(r"^:[A-Za-z_-]+:", stripped):
            continue

        lines.append(line)

    return "\n".join(lines).strip() + "\n"


def normalize_asciidoc(text: str) -> str:
    """Normalize AsciiDoc into text that chunks well for RAG."""

    normalized = _preprocess_asciidoc_tabs(text)
    lines: list[str] = []

    skip_block = False
    for raw_line in normalized.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("ifdef::") or stripped.startswith("ifndef::"):
            skip_block = True
            continue
        if stripped.startswith("endif::"):
            skip_block = False
            continue
        if skip_block:
            continue

        if stripped.startswith(":") and stripped.endswith(":"):
            continue

        include_match = re.match(r"^include::(.+?)\[\]\s*$", stripped)
        if include_match:
            lines.append(f"Include: {include_match.group(1)}")
            continue

        image_match = re.match(r"^image::(.+?)\[(.*?)\]\s*$", stripped)
        if image_match:
            alt = image_match.group(2).strip()
            label = f"Image: {image_match.group(1)}"
            if alt:
                label += f" ({alt})"
            lines.append(label)
            continue

        lines.append(line)

    return "\n".join(lines).strip() + "\n"


def iter_source_sections(document: SourceDocument) -> Iterable[SourceDocument]:
    """Yield heading-aware sections for a supported source document."""

    if document.metadata.get("source_format") == "asciidoc":
        yield from iter_asciidoc_sections(document)
        return

    yield from iter_markdown_sections(document)


def iter_markdown_sections(document: SourceDocument) -> Iterable[SourceDocument]:
    """Yield heading-aware sections for a normalized Markdown document."""

    heading_stack: list[tuple[int, str]] = []
    buffer: list[str] = []
    current_section = document.metadata.get("title", "")

    def flush() -> SourceDocument | None:
        content = "\n".join(buffer).strip()
        if not content:
            return None
        metadata = dict(document.metadata)
        metadata["section"] = current_section
        return SourceDocument(page_content=content + "\n", metadata=metadata)

    for line in document.page_content.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            section = flush()
            if section is not None:
                yield section
            buffer = [line]
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_stack = [(lvl, val) for lvl, val in heading_stack if lvl < level]
            heading_stack.append((level, title))
            current_section = " > ".join(value for _, value in heading_stack)
            continue

        buffer.append(line)

    section = flush()
    if section is not None:
        yield section


def iter_asciidoc_sections(document: SourceDocument) -> Iterable[SourceDocument]:
    """Yield heading-aware sections for a normalized AsciiDoc document."""

    heading_stack: list[tuple[int, str]] = []
    buffer: list[str] = []
    current_section = document.metadata.get("title", "")

    def flush() -> SourceDocument | None:
        content = "\n".join(buffer).strip()
        if not content:
            return None
        metadata = dict(document.metadata)
        metadata["section"] = current_section
        return SourceDocument(page_content=content + "\n", metadata=metadata)

    for line in document.page_content.splitlines():
        heading = re.match(r"^(={1,6})\s+(.+?)\s*$", line)
        if heading:
            section = flush()
            if section is not None:
                yield section
            buffer = [line]
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_stack = [(lvl, val) for lvl, val in heading_stack if lvl < level]
            heading_stack.append((level, title))
            current_section = " > ".join(value for _, value in heading_stack)
            continue

        buffer.append(line)

    section = flush()
    if section is not None:
        yield section


def extract_first_heading(text: str) -> str | None:
    """Return the first Markdown heading title."""

    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return None


def extract_first_asciidoc_heading(text: str) -> str | None:
    """Return the first top-level AsciiDoc heading title."""

    for line in text.splitlines():
        match = re.match(r"^=\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return None


def infer_component(guide: str, stem: str, title: str) -> str:
    """Infer a coarse component label for filtering and incident prompts."""

    haystack = f"{guide} {stem} {title}".lower()
    component_keywords = {
        "persistence": ["persistence", "persistent", "wal", "checkpoint", "персист"],
        "cluster": ["cluster", "topology", "baseline", "discovery", "кластер", "тополог"],
        "rebalance": ["rebalance", "rebalancing", "ребаланс"],
        "security": ["security", "ssl", "tls", "audit", "auth", "безопас", "аудит"],
        "sql": ["sql", "calcite", "jdbc"],
        "rest-api": ["rest-api", "rest api"],
        "monitoring": ["monitoring", "metrics", "grafana", "zabbix", "метрик", "монитор"],
        "performance": ["performance", "tuning", "sysctl", "производ"],
        "installation": ["installation", "ansible", "upgrade", "rollback", "установ"],
        "cdc": ["cdc", "change-data-capture", "репликац"],
        "jvm": ["jvm", "openjdk", "gc", "heap", "heapdump", "safepoint", "commit_memory"],
        "memory": ["memory", "oom", "offheap", "page replacement", "памят", "озу"],
        "network": ["network", "tcp", "socket", "segmented", "rmi", "сеть", "сетев"],
        "incident": ["incident", "jira", "sbtsupport", "ise-"],
    }
    for component, keywords in component_keywords.items():
        if any(keyword in haystack for keyword in keywords):
            return component
    return guide


def _directive_to_text(name: str, value: str) -> str:
    if name == "md-tab-set":
        return ""
    if name == "md-tab-item":
        return f"Tab: {value}" if value else "Tab"
    if name == "admonition":
        return f"Admonition: {value}" if value else "Admonition"
    if name == "code-block":
        return f"Code block: {value}" if value else "Code block"
    if name == "list-table":
        return f"Table: {value}" if value else "Table"
    return f"{name}: {value}" if value else name


def _clean_yaml_scalar(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        return cleaned[1:-1]
    return cleaned


def _read_csv_rows(
    path: Path,
    *,
    required_fields: set[str] | None = None,
) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        fieldnames = set(reader.fieldnames or [])
        missing = (required_fields or set()) - fieldnames
        if missing:
            raise ValueError(
                f"{path.name} is missing columns: {', '.join(sorted(missing))}"
            )
        return list(reader)


def _validate_jira_snapshot_rows(
    issues: list[dict[str, str]],
    comments: list[dict[str, str]],
) -> None:
    issue_keys = [row.get("issue_key", "") for row in issues]
    if not all(issue_keys) or len(issue_keys) != len(set(issue_keys)):
        raise ValueError("Jira snapshot issue_key values must be non-empty and unique")
    comment_ids = [row.get("comment_id", "") for row in comments]
    if not all(comment_ids) or len(comment_ids) != len(set(comment_ids)):
        raise ValueError("Jira snapshot comment_id values must be non-empty and unique")

    schema_versions = {
        row.get("schema_version", "") for row in [*issues, *comments]
    }
    if schema_versions and schema_versions != {"1"}:
        raise ValueError(
            f"Unsupported Jira snapshot schema versions: {sorted(schema_versions)}"
        )

    issue_key_set = set(issue_keys)
    comments_by_issue: dict[str, list[dict[str, str]]] = {}
    for row in comments:
        issue_key = row.get("issue_key", "")
        if issue_key not in issue_key_set:
            raise ValueError(f"Jira snapshot contains an orphan comment for {issue_key}")
        comments_by_issue.setdefault(issue_key, []).append(row)

    for issue in issues:
        issue_key = issue["issue_key"]
        issue_comments = comments_by_issue.get(issue_key, [])
        substantive_count = sum(
            row.get("is_substantive", "").casefold() == "true"
            for row in issue_comments
        )
        if int(issue.get("comment_count") or 0) != len(issue_comments):
            raise ValueError(f"Jira snapshot comment count mismatch for {issue_key}")
        if int(issue.get("substantive_comment_count") or 0) != substantive_count:
            raise ValueError(
                f"Jira snapshot substantive comment count mismatch for {issue_key}"
            )
        for comment in issue_comments:
            if comment.get("support_key", "") != issue.get("support_key", ""):
                raise ValueError(f"Jira snapshot support key mismatch for {issue_key}")


def _jira_snapshot_base_metadata(
    row: dict[str, str],
    *,
    source: str,
    source_type: str,
    variant: str,
    title: str,
    component: str,
    quality_flags: list[str],
) -> dict[str, str]:
    return {
        "source": source,
        "source_path": source,
        "source_type": source_type,
        "source_format": "jira-snapshot",
        "snapshot_variant": variant,
        "doc_set_code": "JIRA",
        "product": "Ignite/DataGrid",
        "product_version": row.get("affected_versions_json", "[]"),
        "release_id": "",
        "archive_group_id": "",
        "guide": "jira",
        "component": component,
        "components": row.get("components_json", "[]"),
        "labels": row.get("labels_json", "[]"),
        "affected_versions": row.get("affected_versions_json", "[]"),
        "fix_versions": row.get("fix_versions_json", "[]"),
        "title": title,
        "issue_key": row.get("issue_key", ""),
        "support_key": row.get("support_key", ""),
        "status": row.get("status", ""),
        "resolution": row.get("resolution", ""),
        "priority": row.get("priority", ""),
        "issue_type": row.get("issue_type", ""),
        "created_at": row.get("created_at", ""),
        "updated_at": row.get("updated_at", ""),
        "resolution_at": row.get("resolution_at", ""),
        "curated_eligible": row.get("curated_eligible", "false"),
        "quality_flags": json.dumps(quality_flags, ensure_ascii=False),
        "jira_url": row.get("jira_url", ""),
    }


def _json_string_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON list in Jira snapshot: {value[:80]}") from error
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("Jira snapshot JSON metadata must contain a list of strings")
    return parsed


def _raise_csv_field_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit / 10)


def _preprocess_asciidoc_tabs(text: str) -> str:
    """Collapse Antora-style tabs to Unix sections when present."""

    had_trailing_newline = text.endswith("\n")
    lines = text.splitlines()
    processed_lines: list[str] = []
    i = 0

    def consume_tabs_block(start_index: int) -> tuple[list[str], int]:
        block_lines: list[str] = []
        idx = start_index + 1

        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1

        if idx >= len(lines):
            return [lines[start_index]], start_index + 1

        end_token = lines[idx].strip()
        if end_token not in {"====", "--"}:
            return [lines[start_index]], start_index + 1

        idx += 1
        while idx < len(lines):
            if lines[idx].strip() == end_token:
                idx += 1
                break
            block_lines.append(lines[idx])
            idx += 1
        else:
            return lines[start_index:idx], idx

        return process_tab_sections(block_lines), idx

    def process_tab_sections(block_body: list[str]) -> list[str]:
        sections: list[tuple[str, list[str]]] = []
        current_tab: str | None = None
        collecting = False
        buffer: list[str] = []

        for line in block_body:
            stripped = line.strip()
            tab_match = re.match(r"tab:([^\[]+)\[\]", stripped)
            if tab_match:
                if collecting and current_tab is not None:
                    sections.append((current_tab, buffer))
                current_tab = tab_match.group(1)
                collecting = False
                buffer = []
                continue

            if stripped == "--":
                if current_tab is None:
                    continue
                if collecting:
                    sections.append((current_tab, buffer))
                    collecting = False
                    current_tab = None
                    buffer = []
                else:
                    collecting = True
                    buffer = []
                continue

            if collecting and current_tab is not None:
                buffer.append(line)

        if collecting and current_tab is not None:
            sections.append((current_tab, buffer))

        selected_sections = [
            tab_lines
            for tab_name, tab_lines in sections
            if tab_name.strip().lower() in {"unix", "linux", "java", "xml"}
        ]
        if not selected_sections:
            selected_sections = [tab_lines for _, tab_lines in sections[:1]]

        output_lines: list[str] = []
        seen_keys: set[str] = set()
        for section in selected_sections:
            key = "\n".join(line.rstrip() for line in section).strip()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if output_lines and output_lines[-1] != "":
                output_lines.append("")
            output_lines.extend(section)

        return output_lines

    while i < len(lines):
        if lines[i].strip() == "[tabs]":
            replacement, next_index = consume_tabs_block(i)
            processed_lines.extend(replacement)
            i = next_index
        else:
            processed_lines.append(lines[i])
            i += 1

    result = "\n".join(processed_lines)
    if had_trailing_newline:
        result += "\n"
    return result


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
