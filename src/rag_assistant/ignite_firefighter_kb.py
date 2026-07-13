"""Load the bundled ignite-firefighter knowledge-base corpora."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import Any


SOURCE_COMMIT = "5cb97512b5ae7e43f9822b7f2ae0b3e9092878f9"
TREE_RELATIVE_PATH = "troubleshooting/ignite-troubleshooting-tree.yaml"
GC_NOTES_RELATIVE_PATH = "troubleshooting/gc-collectors-troubleshooting.md"
STACKOVERFLOW_RELATIVE_PATH = "stackoverflow/answered-questions.combined.jsonl"
MAILING_LIST_RELATIVE_PATH = "mailing-list/answered_threads.mbox.gz"


def load_troubleshooting_tree_source(
    source_path: Path,
    *,
    source_type: str = "ignite-firefighter-tree",
) -> list[object]:
    """Expand the machine-readable tree into independently retrievable records."""

    import yaml

    from rag_assistant.docs import SourceDocument, infer_component

    root, tree_path = _resolve_file(source_path, TREE_RELATIVE_PATH)
    raw = yaml.safe_load(tree_path.read_text(encoding="utf-8-sig")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Troubleshooting tree root must be a mapping: {tree_path}")
    required = {"fact_catalog", "action_catalog", "decision_tree", "checklist_items"}
    missing = required - set(raw)
    if missing:
        raise ValueError(
            "Troubleshooting tree is missing sections: " + ", ".join(sorted(missing))
        )

    source_rel = _project_relative_source(root, TREE_RELATIVE_PATH)
    documents: list[SourceDocument] = []

    for source in raw.get("sources") or []:
        source_id = str(source.get("id") or "").strip()
        if not source_id:
            raise ValueError("Troubleshooting provenance source requires a non-empty id")
        title = str(source.get("title") or source_id)
        body = _yaml_record_text(f"Provenance source: {title}", source)
        documents.append(
            SourceDocument(
                page_content=body,
                metadata=_tree_metadata(
                    source_type=source_type,
                    source_path=f"{source_rel}#source/{source_id}",
                    record_id=f"source:{source_id}",
                    record_type="provenance_source",
                    title=title,
                    component="provenance",
                    quality_score=0.55,
                    source_url=str(source.get("url") or ""),
                ),
            )
        )

    for fact_id, fact in (raw.get("fact_catalog") or {}).items():
        title = str(fact.get("description") or fact_id)
        body = _yaml_record_text(f"Fact: {fact_id}", fact)
        documents.append(
            SourceDocument(
                page_content=body,
                metadata=_tree_metadata(
                    source_type=source_type,
                    source_path=f"{source_rel}#fact/{fact_id}",
                    record_id=f"fact:{fact_id}",
                    record_type="fact",
                    title=title,
                    component=infer_component("troubleshooting", str(fact_id), body),
                    quality_score=0.8,
                ),
            )
        )

    action_catalog = raw.get("action_catalog") or {}
    for action_id, action in action_catalog.items():
        title = str(action.get("title") or action_id)
        body = _yaml_record_text(f"Action: {action_id} — {title}", action)
        documents.append(
            SourceDocument(
                page_content=body,
                metadata=_tree_metadata(
                    source_type=source_type,
                    source_path=f"{source_rel}#action/{action_id}",
                    record_id=f"action:{action_id}",
                    record_type="action",
                    title=title,
                    component=infer_component("troubleshooting", str(action_id), body),
                    quality_score=0.88,
                ),
            )
        )

    decision_tree = raw.get("decision_tree") or {}
    for node_id, node in (decision_tree.get("nodes") or {}).items():
        title = str(node.get("title") or node_id)
        resolved = dict(node)
        recommendation = dict(resolved.get("recommendation") or {})
        action_id = str(recommendation.get("action") or "")
        if action_id:
            action = action_catalog.get(action_id)
            if action is None:
                raise ValueError(
                    f"Decision node {node_id} references unknown action {action_id}"
                )
            recommendation["resolved_action"] = action
            resolved["recommendation"] = recommendation
        body = _yaml_record_text(f"Decision node: {node_id} — {title}", resolved)
        documents.append(
            SourceDocument(
                page_content=body,
                metadata=_tree_metadata(
                    source_type=source_type,
                    source_path=f"{source_rel}#node/{node_id}",
                    record_id=f"node:{node_id}",
                    record_type="decision_node",
                    title=title,
                    component=infer_component("troubleshooting", str(node_id), body),
                    quality_score=0.9,
                ),
            )
        )

    for checklist_id, checklist in (raw.get("checklist_items") or {}).items():
        title = str(checklist.get("title") or checklist_id)
        body = _yaml_record_text(f"Checklist: {checklist_id} — {title}", checklist)
        documents.append(
            SourceDocument(
                page_content=body,
                metadata=_tree_metadata(
                    source_type=source_type,
                    source_path=f"{source_rel}#checklist/{checklist_id}",
                    record_id=f"checklist:{checklist_id}",
                    record_type="checklist",
                    title=title,
                    component=infer_component("troubleshooting", str(checklist_id), body),
                    quality_score=0.82,
                ),
            )
        )

    expected_count = (
        len(raw.get("sources") or [])
        + len(raw.get("fact_catalog") or {})
        + len(action_catalog)
        + len(decision_tree.get("nodes") or {})
        + len(raw.get("checklist_items") or {})
    )
    if len(documents) != expected_count:
        raise ValueError("Troubleshooting tree expansion produced an unexpected count")
    return documents


def load_gc_notes_source(
    source_path: Path,
    *,
    source_type: str = "ignite-firefighter-notes",
) -> list[object]:
    """Load the curated collector-specific troubleshooting note."""

    from rag_assistant.docs import SourceDocument, extract_first_heading, normalize_markdown

    root, notes_path = _resolve_file(source_path, GC_NOTES_RELATIVE_PATH)
    text = normalize_markdown(notes_path.read_text(encoding="utf-8-sig"))
    source_rel = _project_relative_source(root, GC_NOTES_RELATIVE_PATH)
    return [
        SourceDocument(
            page_content=text,
            metadata={
                "source": source_rel,
                "source_path": source_rel,
                "source_url": "",
                "source_type": source_type,
                "source_format": "markdown",
                "source_commit": SOURCE_COMMIT,
                "record_id": "gc-collectors-troubleshooting",
                "record_type": "curated_note",
                "title": extract_first_heading(text) or "GC Collectors Troubleshooting Notes",
                "section": "GC Collectors Troubleshooting Notes",
                "guide": "troubleshooting",
                "component": "jvm",
                "product": "Apache Ignite",
                "product_version": "Ignite 2.x",
                "language": "en",
                "trust_tier": "curated",
                "authority_score": 0.85,
                "quality_score": 0.9,
                "license": "Apache-2.0",
                "collector": "G1|Shenandoah|ZGC",
                "jdk_version": "11|21|collector-dependent",
            },
        )
    ]


def load_stackoverflow_kb_source(
    source_path: Path,
    *,
    source_type: str = "stackoverflow-kb",
) -> list[object]:
    """Load every answer/comment as a question-and-response retrieval record."""

    from rag_assistant.docs import SourceDocument, infer_component

    root, jsonl_path = _resolve_file(source_path, STACKOVERFLOW_RELATIVE_PATH)
    manifest_path = jsonl_path.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    expected_records = int(manifest.get("records") or 0)
    source_rel = _project_relative_source(root, STACKOVERFLOW_RELATIVE_PATH)
    documents: list[SourceDocument] = []
    record_count = 0

    with jsonl_path.open(encoding="utf-8-sig") as file_obj:
        for line_number, raw_line in enumerate(file_obj, start=1):
            if not raw_line.strip():
                continue
            record_count += 1
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL record at line {line_number}") from exc
            _validate_qa_record(record, line_number=line_number)

            source_name = str(record["source"])
            question_id = str(record["id"])
            title = str(record.get("title") or question_id)
            tags = [str(tag) for tag in (record.get("tags") or record.get("labels") or [])]
            question = record.get("question") or {}
            body_format = str(record.get("body_format") or "markdown")
            question_text = _normalize_community_body(
                str(question.get("body") or ""), body_format=body_format
            )

            for response_index, response in enumerate(record.get("responses") or [], start=1):
                response_id = str(response.get("id") or response_index)
                response_text = _normalize_community_body(
                    str(response.get("body") or ""), body_format=body_format
                )
                if not response_text.strip():
                    continue
                source_url = _response_url(record, response)
                is_accepted = bool(response.get("is_accepted"))
                answer_score = _safe_int(response.get("score"))
                question_score = _safe_int(record.get("score"))
                quality_score = _community_quality_score(
                    is_accepted=is_accepted,
                    answer_score=answer_score,
                    question_score=question_score,
                    source=source_name,
                )
                record_id = f"{source_name}:{question_id}:response:{response_id}"
                version_text = _extract_product_versions(
                    f"{title}\n{question_text[:5000]}\n{response_text[:5000]}"
                )
                page_content = (
                    f"# {title}\n\n"
                    f"Source: {source_name}\n"
                    f"Tags: {' | '.join(tags) if tags else 'none'}\n\n"
                    f"## Question\n\n{question_text.strip()}\n\n"
                    f"## Response\n\n{response_text.strip()}\n"
                )
                documents.append(
                    SourceDocument(
                        page_content=page_content,
                        metadata={
                            "source": source_url or str(record.get("url") or source_rel),
                            "source_path": f"{source_rel}#{record_id}",
                            "source_url": source_url or str(record.get("url") or ""),
                            "source_type": source_type,
                            "source_format": "qa-pair",
                            "source_commit": SOURCE_COMMIT,
                            "record_id": record_id,
                            "record_type": str(record.get("kind") or "answered_question"),
                            "thread_id": f"{source_name}:{question_id}",
                            "question_id": question_id,
                            "response_id": response_id,
                            "title": title,
                            "section": "Question and response",
                            "guide": "community",
                            "component": infer_component(
                                "community", " ".join(tags), f"{title} {question_text[:1000]}"
                            ),
                            "product": "Apache Ignite",
                            "product_version": version_text,
                            "language": "en",
                            "tags": "|".join(tags),
                            "published_at": str(response.get("created_at") or record.get("created_at") or ""),
                            "updated_at": str(response.get("updated_at") or record.get("updated_at") or ""),
                            "author": str(response.get("author") or ""),
                            "is_accepted": is_accepted,
                            "question_score": question_score,
                            "answer_score": answer_score,
                            "quality_score": quality_score,
                            "trust_tier": "community",
                            "authority_score": 0.35 if is_accepted else 0.2,
                            "license": "CC BY-SA" if source_name == "stackoverflow" else "upstream",
                        },
                    )
                )

    if expected_records and record_count != expected_records:
        raise ValueError(
            f"StackOverflow manifest expects {expected_records} records, got {record_count}"
        )
    return documents


def load_mailing_list_source(
    source_path: Path,
    *,
    source_type: str = "ignite-user-mailing-list",
) -> list[object]:
    """Load cleaned public user-list messages with stable thread metadata."""

    from rag_assistant.docs import SourceDocument, infer_component

    root, mbox_path = _resolve_file(source_path, MAILING_LIST_RELATIVE_PATH)
    manifest = json.loads(
        (mbox_path.parent / "manifest.json").read_text(encoding="utf-8-sig")
    )
    raw_mbox = gzip.decompress(mbox_path.read_bytes())
    raw_messages = _split_mbox(raw_mbox)
    expected_messages = int(manifest.get("messages") or 0)
    if expected_messages and len(raw_messages) != expected_messages:
        raise ValueError(
            f"Mailing-list manifest expects {expected_messages} messages, got {len(raw_messages)}"
        )

    source_rel = _project_relative_source(root, MAILING_LIST_RELATIVE_PATH)
    documents: list[SourceDocument] = []
    subject_occurrences: dict[str, int] = defaultdict(int)
    for raw_message in raw_messages:
        message = BytesParser(policy=policy.default).parsebytes(raw_message)
        subject = _clean_header(str(message.get("Subject") or "Untitled Ignite discussion"))
        normalized_subject = _normalize_subject(subject)
        thread_id = hashlib.sha1(normalized_subject.encode("utf-8")).hexdigest()
        subject_occurrences[thread_id] += 1
        message_id = str(message.get("Message-Id") or "").strip(" <>\t\r\n")
        if not message_id:
            message_id = f"{thread_id}-{subject_occurrences[thread_id]}"
        body = _clean_mail_body(_message_text(message))
        if len(re.sub(r"\s+", "", body)) < 30:
            continue
        display_name, _ = parseaddr(str(message.get("From") or ""))
        author = _redact_email(display_name.strip())
        published_at = _mail_date(str(message.get("Date") or ""))
        record_id = f"mail:{hashlib.sha1(message_id.encode('utf-8')).hexdigest()}"
        page_content = (
            f"# {subject}\n\n"
            f"Thread: {normalized_subject}\n"
            f"Date: {published_at or 'unknown'}\n"
            f"Author: {author or 'unknown'}\n\n"
            f"{body.strip()}\n"
        )
        documents.append(
            SourceDocument(
                page_content=page_content,
                metadata={
                    "source": f"mailing-list://user@ignite.apache.org/{thread_id}",
                    "source_path": f"{source_rel}#{record_id}",
                    "source_url": "https://lists.apache.org/list.html?user@ignite.apache.org",
                    "source_type": source_type,
                    "source_format": "mail-message",
                    "source_commit": SOURCE_COMMIT,
                    "record_id": record_id,
                    "record_type": "mailing_list_message",
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "title": subject,
                    "section": normalized_subject,
                    "guide": "community",
                    "component": infer_component("community", normalized_subject, body[:1000]),
                    "product": "Apache Ignite",
                    "product_version": _extract_product_versions(f"{subject}\n{body[:5000]}"),
                    "language": "mixed",
                    "published_at": published_at,
                    "author": author,
                    "quality_score": 0.45,
                    "trust_tier": "experimental",
                    "authority_score": 0.05,
                    "license": "Apache public mailing-list archive",
                },
            )
        )
    return documents


def _tree_metadata(
    *,
    source_type: str,
    source_path: str,
    record_id: str,
    record_type: str,
    title: str,
    component: str,
    quality_score: float,
    source_url: str = "",
) -> dict[str, Any]:
    return {
        "source": source_url or source_path,
        "source_path": source_path,
        "source_url": source_url,
        "source_type": source_type,
        "source_format": "decision-record",
        "source_commit": SOURCE_COMMIT,
        "record_id": record_id,
        "record_type": record_type,
        "title": title,
        "section": title,
        "guide": "troubleshooting",
        "component": component,
        "product": "Apache Ignite",
        "product_version": "Ignite 2.x",
        "language": "ru|en",
        "trust_tier": "curated",
        "authority_score": 0.8,
        "quality_score": quality_score,
        "license": "Apache-2.0",
        "published_at": "2026-06-07",
    }


def _yaml_record_text(heading: str, record: Any) -> str:
    import yaml

    payload = yaml.safe_dump(
        record,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"# {heading}\n\n{payload}\n"


def _resolve_file(source_path: Path, relative_path: str) -> tuple[Path, Path]:
    resolved = source_path.expanduser().resolve()
    if resolved.is_file():
        return resolved.parent, resolved
    candidate = resolved / relative_path
    if not candidate.is_file():
        raise FileNotFoundError(f"Knowledge-base file not found: {candidate}")
    _validate_bundled_checksum(resolved, relative_path, candidate)
    return resolved, candidate


def _validate_bundled_checksum(root: Path, relative_path: str, candidate: Path) -> None:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {
        str(entry.get("path")): str(entry.get("sha256") or "")
        for entry in manifest.get("files") or []
        if isinstance(entry, dict)
    }
    expected = entries.get(relative_path)
    if not expected:
        raise ValueError(f"Bundle manifest has no checksum for {relative_path}")
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(
            f"Knowledge-base checksum mismatch for {relative_path}: {actual} != {expected}"
        )


def _project_relative_source(root: Path, relative_path: str) -> str:
    candidate = root / relative_path
    if not candidate.exists():
        candidate = root / Path(relative_path).name
    try:
        project_root = Path(__file__).resolve().parents[2]
        return candidate.relative_to(project_root).as_posix()
    except ValueError:
        return candidate.as_posix()


def _validate_qa_record(record: Any, *, line_number: int) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"JSONL line {line_number} must contain an object")
    required = {"source", "id", "title", "question", "responses"}
    missing = required - set(record)
    if missing:
        raise ValueError(
            f"JSONL line {line_number} is missing: {', '.join(sorted(missing))}"
        )
    if not isinstance(record.get("responses"), list):
        raise ValueError(f"JSONL line {line_number} responses must be a list")


def _normalize_community_body(text: str, *, body_format: str) -> str:
    if body_format.lower() == "html":
        from rag_assistant.confluence import html_fragment_to_markdown

        normalized = html_fragment_to_markdown(text)
    else:
        normalized = text.strip() + "\n"
    return _redact_obvious_secrets(normalized)


def _response_url(record: dict[str, Any], response: dict[str, Any]) -> str:
    explicit = str(response.get("url") or "")
    if explicit:
        return explicit
    response_id = str(response.get("id") or "")
    if record.get("source") == "stackoverflow" and response_id:
        return f"https://stackoverflow.com/a/{response_id}"
    return str(record.get("url") or "")


def _community_quality_score(
    *,
    is_accepted: bool,
    answer_score: int,
    question_score: int,
    source: str,
) -> float:
    score = 0.42
    if is_accepted:
        score += 0.25
    score += max(-0.1, min(0.2, answer_score * 0.04))
    score += max(-0.05, min(0.08, question_score * 0.015))
    if source == "github":
        score -= 0.08
    return round(max(0.1, min(0.95, score)), 3)


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _extract_product_versions(text: str) -> str:
    versions = re.findall(
        r"(?i)\b(?:apache\s+ignite|ignite|gridgain)(?:\s+version|\s+ver\.?|\s+v)?\s*[:=]?\s*(\d+\.\d+(?:\.\d+)?)",
        text,
    )
    unique = list(dict.fromkeys(versions))
    return "|".join(unique[:6])


def _split_mbox(raw_mbox: bytes) -> list[bytes]:
    chunks = re.split(rb"(?m)^From [^\n]*\n", raw_mbox)
    return [chunk for chunk in chunks[1:] if chunk.strip()]


def _message_text(message: Any) -> str:
    parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() != "text/plain":
                continue
            if str(part.get_content_disposition() or "") == "attachment":
                continue
            try:
                parts.append(str(part.get_content()))
            except (LookupError, UnicodeDecodeError):
                payload = part.get_payload(decode=True) or b""
                parts.append(payload.decode("utf-8", errors="replace"))
    else:
        try:
            parts.append(str(message.get_content()))
        except (LookupError, UnicodeDecodeError):
            payload = message.get_payload(decode=True) or b""
            parts.append(payload.decode("utf-8", errors="replace"))
    return "\n".join(parts)


def _clean_mail_body(text: str) -> str:
    lines: list[str] = []
    for line in text.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if stripped == "--":
            break
        if line.lstrip().startswith(">"):
            continue
        if re.match(r"(?i)^on .+ wrote:$", stripped):
            continue
        if re.match(r"(?i)^-{2,}\s*original message\s*-{2,}$", stripped):
            break
        if "To unsubscribe" in line or "mailing list" in line.lower() and "unsubscribe" in line.lower():
            continue
        lines.append(_redact_email(line.rstrip()))
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return _redact_obvious_secrets(cleaned)


def _clean_header(value: str) -> str:
    return re.sub(r"\s+", " ", _redact_email(value)).strip()


def _normalize_subject(subject: str) -> str:
    normalized = re.sub(r"(?i)^\s*(?:(?:re|fwd?)\s*:\s*)+", "", subject)
    return re.sub(r"\s+", " ", normalized).strip() or "Untitled Ignite discussion"


def _redact_email(text: str) -> str:
    return re.sub(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[REDACTED EMAIL]",
        text,
    )


def _redact_obvious_secrets(text: str) -> str:
    redacted = re.sub(
        r"(?is)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        "[REDACTED PRIVATE KEY]",
        text,
    )
    redacted = re.sub(
        r"(?im)^(\s*(?:authorization|password|passwd|api[_-]?key|client[_-]?secret|token)\s*[:=]\s*)\S+",
        r"\1[REDACTED]",
        redacted,
    )
    return redacted


def _mail_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        if parsed is None:
            return ""
        return parsed.isoformat()
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value).isoformat()
        except ValueError:
            return ""
