"""Export SBTSUPPORT Jira tickets into validated full and curated snapshots."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Iterable
import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry

from rag_assistant.config import load_config


SCHEMA_VERSION = "1"
JIRA_USERNAME_ENV = "RAG_ASSISTANT_JIRA_USERNAME"
JIRA_PASSWORD_ENV = "RAG_ASSISTANT_JIRA_PASSWORD"
SUPPORT_TAG_RE = re.compile(r"^\[SBTSUPPORT-\d+\]")
SUPPORT_KEY_RE = re.compile(r"SBTSUPPORT-\d+")
SUBSTANTIVE_COMMENT_MIN_CHARS = 30
REQUEST_TIMEOUT_SECONDS = 60
PAGE_SIZE = 100

EXCLUDED_STATUSES = {"cancelled", "отклонен исполнителем"}
EXCLUDED_RESOLUTIONS = {"дубликат", "отклонен", "неполный"}

ISSUE_FIELDS = [
    "summary",
    "description",
    "status",
    "resolution",
    "priority",
    "issuetype",
    "created",
    "updated",
    "resolutiondate",
    "components",
    "labels",
    "versions",
    "fixVersions",
    "attachment",
]

ISSUE_COLUMNS = [
    "schema_version",
    "issue_key",
    "support_key",
    "summary",
    "description",
    "status",
    "resolution",
    "priority",
    "issue_type",
    "created_at",
    "updated_at",
    "resolution_at",
    "components_json",
    "labels_json",
    "affected_versions_json",
    "fix_versions_json",
    "attachments_json",
    "comment_count",
    "substantive_comment_count",
    "has_description",
    "has_comments",
    "has_resolution",
    "curated_eligible",
    "quality_flags_json",
    "summary_redaction_count",
    "description_redaction_count",
    "jira_url",
]

COMMENT_COLUMNS = [
    "schema_version",
    "issue_key",
    "support_key",
    "comment_id",
    "sequence",
    "author",
    "created_at",
    "updated_at",
    "body",
    "is_substantive",
    "redaction_count",
]

PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----.*?"
    r"-----END (?:[A-Z0-9]+ )?PRIVATE KEY-----",
    re.DOTALL,
)
AUTHORIZATION_RE = re.compile(
    r"(?im)^(\s*Authorization\s*:\s*)(?:Basic|Bearer)\s+\S+"
)
JWT_RE = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
    r"(?![A-Za-z0-9_-])"
)
QUOTED_SECRET_RE = re.compile(
    r"(?i)([\"']?(?:password|passwd|token|secret|api_key|client_secret)[\"']?"
    r"\s*[:=]\s*)([\"'])(.*?)\2"
)
UNQUOTED_SECRET_RE = re.compile(
    r"(?i)(\b(?:password|passwd|token|secret|api_key|client_secret)\b"
    r"\s*[:=]\s*)([^\s,;\"']+)"
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def raise_csv_field_limit() -> None:
    """Allow validation to read large Jira description/comment CSV fields."""

    limit = os.sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit / 10)


def build_session(
    *,
    cert_path: Path,
    username: str | None = None,
    password: str | None = None,
) -> requests.Session:
    """Create an authenticated Jira session with retries for transient failures."""

    if not cert_path.is_file():
        raise FileNotFoundError(f"Client certificate not found: {cert_path}")
    username = username or os.getenv(JIRA_USERNAME_ENV)
    password = password or os.getenv(JIRA_PASSWORD_ENV)
    if not username or not password:
        raise RuntimeError(
            f"Set {JIRA_USERNAME_ENV} and {JIRA_PASSWORD_ENV} before exporting Jira snapshots."
        )

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)
    session.auth = (username, password)
    session.cert = str(cert_path)
    session.verify = False
    return session


def request_json(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any],
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Execute one Jira GET request and return a JSON object."""

    response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object from Jira endpoint: {url}")
    return payload


def iter_matching_issues(
    session: requests.Session,
    *,
    base_url: str,
    jql: str,
    page_size: int = PAGE_SIZE,
) -> Iterable[dict[str, Any]]:
    """Yield every issue whose summary starts with a strict SBTSUPPORT tag."""

    start_at = 0
    while True:
        page = request_json(
            session,
            f"{base_url}/rest/api/2/search",
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "fields": ",".join(ISSUE_FIELDS),
            },
        )
        issues = page.get("issues") or []
        if not isinstance(issues, list):
            raise ValueError("Jira search response contains an invalid issues field")

        for issue in issues:
            fields = issue.get("fields") or {}
            if SUPPORT_TAG_RE.match(str(fields.get("summary") or "")):
                yield issue

        total = int(page.get("total") or 0)
        if not issues or start_at + len(issues) >= total:
            return
        start_at += len(issues)


def fetch_all_comments(
    session: requests.Session,
    *,
    base_url: str,
    issue_key: str,
    page_size: int = PAGE_SIZE,
) -> list[dict[str, Any]]:
    """Fetch every comment for one issue using Jira comment pagination."""

    comments: list[dict[str, Any]] = []
    start_at = 0
    while True:
        page = request_json(
            session,
            f"{base_url}/rest/api/2/issue/{issue_key}/comment",
            params={"startAt": start_at, "maxResults": page_size},
        )
        page_comments = page.get("comments") or []
        if not isinstance(page_comments, list):
            raise ValueError(f"Invalid comments field for Jira issue {issue_key}")
        comments.extend(page_comments)

        total = int(page.get("total") or 0)
        if not page_comments or start_at + len(page_comments) >= total:
            return comments
        start_at += len(page_comments)


def redact_secrets(text: str) -> tuple[str, int]:
    """Mask explicit credentials while preserving ordinary logs and commands."""

    redacted = text or ""
    count = 0

    redacted, replacements = PRIVATE_KEY_RE.subn("[REDACTED PRIVATE KEY]", redacted)
    count += replacements
    redacted, replacements = AUTHORIZATION_RE.subn(
        lambda match: f"{match.group(1)}[REDACTED]", redacted
    )
    count += replacements
    redacted, replacements = JWT_RE.subn("[REDACTED JWT]", redacted)
    count += replacements
    redacted, replacements = QUOTED_SECRET_RE.subn(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]{match.group(2)}",
        redacted,
    )
    count += replacements
    redacted, replacements = UNQUOTED_SECRET_RE.subn(
        lambda match: f"{match.group(1)}[REDACTED]", redacted
    )
    count += replacements
    return redacted, count


def is_substantive_comment(text: str) -> bool:
    """Return whether a comment contains enough non-whitespace content."""

    return len(re.sub(r"\s+", "", text or "")) >= SUBSTANTIVE_COMMENT_MIN_CHARS


def build_snapshot_rows(
    issue: dict[str, Any],
    comments: list[dict[str, Any]],
    *,
    base_url: str,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Normalize one Jira issue and its comments into snapshot CSV rows."""

    fields = issue.get("fields") or {}
    issue_key = str(issue.get("key") or "").strip()
    if not issue_key:
        raise ValueError("Jira issue is missing its key")

    raw_summary = str(fields.get("summary") or "")
    support_match = SUPPORT_KEY_RE.search(raw_summary)
    support_key = support_match.group(0) if support_match else ""
    summary, summary_redactions = redact_secrets(raw_summary)
    description, description_redactions = redact_secrets(
        str(fields.get("description") or "")
    )

    comment_rows: list[dict[str, str]] = []
    substantive_count = 0
    seen_comment_ids: set[str] = set()
    for sequence, comment in enumerate(comments, start=1):
        comment_id = str(comment.get("id") or "").strip()
        if not comment_id:
            raise ValueError(f"Jira issue {issue_key} contains a comment without an id")
        if comment_id in seen_comment_ids:
            raise ValueError(f"Duplicate comment id {comment_id} in Jira issue {issue_key}")
        seen_comment_ids.add(comment_id)

        body, redaction_count = redact_secrets(str(comment.get("body") or ""))
        substantive = is_substantive_comment(body)
        substantive_count += int(substantive)
        author = comment.get("author") or {}
        author_name = ""
        if isinstance(author, dict):
            author_name = str(author.get("displayName") or author.get("name") or "")

        comment_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "issue_key": issue_key,
                "support_key": support_key,
                "comment_id": comment_id,
                "sequence": str(sequence),
                "author": author_name,
                "created_at": str(comment.get("created") or ""),
                "updated_at": str(comment.get("updated") or ""),
                "body": body,
                "is_substantive": _bool_string(substantive),
                "redaction_count": str(redaction_count),
            }
        )

    status = _named_field(fields.get("status"))
    resolution = _named_field(fields.get("resolution"))
    has_description = bool(description.strip())
    has_comments = bool(comment_rows)

    quality_flags: list[str] = []
    if not has_description:
        quality_flags.append("missing_description")
    if not has_comments:
        quality_flags.append("no_comments")
    if substantive_count == 0:
        quality_flags.append("no_substantive_comments")
    if not resolution:
        quality_flags.append("missing_resolution")
    if status.casefold() in EXCLUDED_STATUSES:
        quality_flags.append("excluded_status")
    if resolution.casefold() in EXCLUDED_RESOLUTIONS:
        quality_flags.append("excluded_resolution")

    curated_eligible = (
        has_description
        and substantive_count > 0
        and status.casefold() not in EXCLUDED_STATUSES
        and resolution.casefold() not in EXCLUDED_RESOLUTIONS
    )

    issue_row = {
        "schema_version": SCHEMA_VERSION,
        "issue_key": issue_key,
        "support_key": support_key,
        "summary": summary,
        "description": description,
        "status": status,
        "resolution": resolution,
        "priority": _named_field(fields.get("priority")),
        "issue_type": _named_field(fields.get("issuetype")),
        "created_at": str(fields.get("created") or ""),
        "updated_at": str(fields.get("updated") or ""),
        "resolution_at": str(fields.get("resolutiondate") or ""),
        "components_json": _names_json(fields.get("components")),
        "labels_json": _strings_json(fields.get("labels")),
        "affected_versions_json": _names_json(fields.get("versions")),
        "fix_versions_json": _names_json(fields.get("fixVersions")),
        "attachments_json": _attachments_json(fields.get("attachment")),
        "comment_count": str(len(comment_rows)),
        "substantive_comment_count": str(substantive_count),
        "has_description": _bool_string(has_description),
        "has_comments": _bool_string(has_comments),
        "has_resolution": _bool_string(bool(resolution)),
        "curated_eligible": _bool_string(curated_eligible),
        "quality_flags_json": json.dumps(quality_flags, ensure_ascii=False),
        "summary_redaction_count": str(summary_redactions),
        "description_redaction_count": str(description_redactions),
        "jira_url": f"{base_url}/browse/{issue_key}",
    }
    return issue_row, comment_rows


def collect_snapshot_rows(
    session: requests.Session,
    *,
    base_url: str,
    jql: str,
    page_size: int = PAGE_SIZE,
    limit: int | None = None,
    progress: Any | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Collect normalized issue and comment rows from Jira."""

    issue_rows: list[dict[str, str]] = []
    comment_rows: list[dict[str, str]] = []
    for index, issue in enumerate(
        iter_matching_issues(
            session,
            base_url=base_url,
            jql=jql,
            page_size=page_size,
        ),
        start=1,
    ):
        issue_key = str(issue.get("key") or "")
        comments = fetch_all_comments(
            session,
            base_url=base_url,
            issue_key=issue_key,
            page_size=page_size,
        )
        issue_row, normalized_comments = build_snapshot_rows(
            issue,
            comments,
            base_url=base_url,
        )
        issue_rows.append(issue_row)
        comment_rows.extend(normalized_comments)
        if progress and (index == 1 or index % 10 == 0):
            progress(
                f"Collected {index} tickets and {len(comment_rows)} comments..."
            )
        if limit is not None and index >= limit:
            return issue_rows, comment_rows

    return issue_rows, comment_rows


def write_snapshot(
    *,
    output_root: Path,
    issue_rows: list[dict[str, str]],
    comment_rows: list[dict[str, str]],
    base_url: str,
    jql: str,
    generated_at: datetime | None = None,
) -> Path:
    """Write and atomically publish one validated full/curated snapshot."""

    generated_at = generated_at or datetime.now(timezone.utc)
    timestamp = generated_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root = output_root.resolve()
    snapshots_root = output_root / "snapshots"
    snapshots_root.mkdir(parents=True, exist_ok=True)

    final_dir = snapshots_root / timestamp
    if final_dir.exists():
        final_dir = snapshots_root / f"{timestamp}-{uuid.uuid4().hex[:8]}"
    staging_dir = snapshots_root / f".tmp-{final_dir.name}-{uuid.uuid4().hex}"
    moved_to_final = False

    try:
        full_dir = staging_dir / "full"
        curated_dir = staging_dir / "curated"
        full_dir.mkdir(parents=True)
        curated_dir.mkdir(parents=True)

        curated_issue_rows = [
            row for row in issue_rows if row["curated_eligible"] == "true"
        ]
        curated_keys = {row["issue_key"] for row in curated_issue_rows}
        curated_comment_rows = [
            row for row in comment_rows if row["issue_key"] in curated_keys
        ]

        _write_csv(full_dir / "issues.csv", ISSUE_COLUMNS, issue_rows)
        _write_csv(full_dir / "comments.csv", COMMENT_COLUMNS, comment_rows)
        _write_csv(curated_dir / "issues.csv", ISSUE_COLUMNS, curated_issue_rows)
        _write_csv(curated_dir / "comments.csv", COMMENT_COLUMNS, curated_comment_rows)

        relative_files = [
            Path("full/issues.csv"),
            Path("full/comments.csv"),
            Path("curated/issues.csv"),
            Path("curated/comments.csv"),
        ]
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at.astimezone(timezone.utc).isoformat(),
            "base_jira_url": base_url,
            "jql": jql,
            "support_summary_pattern": SUPPORT_TAG_RE.pattern,
            "substantive_comment_min_non_whitespace_chars": (
                SUBSTANTIVE_COMMENT_MIN_CHARS
            ),
            "curated_policy": {
                "requires_description": True,
                "requires_substantive_comment": True,
                "excluded_statuses": sorted(EXCLUDED_STATUSES),
                "excluded_resolutions": sorted(EXCLUDED_RESOLUTIONS),
                "requires_resolution": False,
            },
            "counts": {
                "full_issues": len(issue_rows),
                "full_comments": len(comment_rows),
                "curated_issues": len(curated_issue_rows),
                "curated_comments": len(curated_comment_rows),
            },
            "sha256": {
                str(path): _sha256(staging_dir / path) for path in relative_files
            },
        }
        (staging_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        validate_snapshot(staging_dir)
        os.replace(staging_dir, final_dir)
        moved_to_final = True
        _replace_latest_symlink(output_root, final_dir)
        return final_dir
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if moved_to_final and final_dir.exists():
            shutil.rmtree(final_dir)
        raise


def validate_snapshot(snapshot_dir: Path) -> None:
    """Validate snapshot referential integrity, counts, and checksums."""

    manifest_path = snapshot_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    variants: dict[str, tuple[list[dict[str, str]], list[dict[str, str]]]] = {}

    for variant in ("full", "curated"):
        issues = _read_csv(snapshot_dir / variant / "issues.csv")
        comments = _read_csv(snapshot_dir / variant / "comments.csv")
        _validate_rows(issues, comments, variant=variant)
        variants[variant] = (issues, comments)

    full_keys = {row["issue_key"] for row in variants["full"][0]}
    curated_keys = {row["issue_key"] for row in variants["curated"][0]}
    if not curated_keys <= full_keys:
        raise ValueError("Curated issues are not a subset of full issues")

    expected_counts = {
        "full_issues": len(variants["full"][0]),
        "full_comments": len(variants["full"][1]),
        "curated_issues": len(variants["curated"][0]),
        "curated_comments": len(variants["curated"][1]),
    }
    if manifest.get("counts") != expected_counts:
        raise ValueError("Snapshot manifest counts do not match CSV contents")

    for relative_path, expected_hash in (manifest.get("sha256") or {}).items():
        if _sha256(snapshot_dir / relative_path) != expected_hash:
            raise ValueError(f"Snapshot checksum mismatch: {relative_path}")


def export_snapshot(
    session: requests.Session,
    *,
    output_root: Path,
    base_url: str,
    jql: str,
    page_size: int = PAGE_SIZE,
    limit: int | None = None,
    progress: Any | None = None,
) -> Path:
    """Collect Jira data and publish a complete snapshot."""

    issues, comments = collect_snapshot_rows(
        session,
        base_url=base_url,
        jql=jql,
        page_size=page_size,
        limit=limit,
        progress=progress,
    )
    return write_snapshot(
        output_root=output_root,
        issue_rows=issues,
        comment_rows=comments,
        base_url=base_url,
        jql=jql,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export SBTSUPPORT Jira tickets into full and curated snapshots."
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--jira-base", default=None)
    parser.add_argument("--jql", default=None)
    parser.add_argument("--cert-path", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--page-size", type=int, default=PAGE_SIZE)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only export this many matching SBTSUPPORT tickets for smoke testing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    base_url = args.jira_base or config.jira.base_url
    jql = args.jql or config.jira.jql
    cert_path = args.cert_path or config.jira.cert_path
    output_root = args.output_root or config.jira.output_root
    if not base_url:
        raise RuntimeError("Set jira.base_url in config or pass --jira-base.")
    if not jql:
        raise RuntimeError("Set jira.jql in config or pass --jql.")
    if cert_path is None:
        raise RuntimeError("Set jira.cert_path in config or pass --cert-path.")

    session = build_session(cert_path=cert_path)
    snapshot_dir = export_snapshot(
        session,
        output_root=output_root,
        base_url=base_url.rstrip("/"),
        jql=jql,
        page_size=args.page_size,
        limit=args.limit,
        progress=lambda message: print(message, flush=True),
    )
    print(f"Published Jira snapshot: {snapshot_dir}")
    return 0


def _validate_rows(
    issues: list[dict[str, str]],
    comments: list[dict[str, str]],
    *,
    variant: str,
) -> None:
    issue_keys = [row.get("issue_key", "") for row in issues]
    if not all(issue_keys) or len(issue_keys) != len(set(issue_keys)):
        raise ValueError(f"{variant}: issue_key values must be non-empty and unique")

    comment_ids = [row.get("comment_id", "") for row in comments]
    if not all(comment_ids) or len(comment_ids) != len(set(comment_ids)):
        raise ValueError(f"{variant}: comment_id values must be non-empty and unique")

    issue_key_set = set(issue_keys)
    comments_by_issue: dict[str, list[dict[str, str]]] = {}
    for row in comments:
        issue_key = row.get("issue_key", "")
        if issue_key not in issue_key_set:
            raise ValueError(f"{variant}: orphan comment for issue {issue_key}")
        comments_by_issue.setdefault(issue_key, []).append(row)

    for issue in issues:
        issue_comments = comments_by_issue.get(issue["issue_key"], [])
        substantive = sum(
            row.get("is_substantive", "").lower() == "true" for row in issue_comments
        )
        if int(issue.get("comment_count") or 0) != len(issue_comments):
            raise ValueError(f"{variant}: comment count mismatch for {issue['issue_key']}")
        if int(issue.get("substantive_comment_count") or 0) != substantive:
            raise ValueError(
                f"{variant}: substantive comment count mismatch for {issue['issue_key']}"
            )


def _replace_latest_symlink(output_root: Path, final_dir: Path) -> None:
    latest_path = output_root / "latest"
    temporary_link = output_root / f".latest-{uuid.uuid4().hex}"
    relative_target = Path("snapshots") / final_dir.name
    os.symlink(relative_target, temporary_link)
    try:
        os.replace(temporary_link, latest_path)
    finally:
        if temporary_link.is_symlink():
            temporary_link.unlink()


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    raise_csv_field_limit()
    with path.open(encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for block in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _named_field(value: Any) -> str:
    return str(value.get("name") or "") if isinstance(value, dict) else ""


def _names_json(values: Any) -> str:
    names = [
        str(value.get("name") or "")
        for value in (values or [])
        if isinstance(value, dict) and value.get("name")
    ]
    return json.dumps(names, ensure_ascii=False)


def _strings_json(values: Any) -> str:
    return json.dumps([str(value) for value in (values or [])], ensure_ascii=False)


def _attachments_json(values: Any) -> str:
    attachments = []
    for value in values or []:
        if not isinstance(value, dict):
            continue
        attachments.append(
            {
                "id": str(value.get("id") or ""),
                "filename": str(value.get("filename") or ""),
                "mime_type": str(value.get("mimeType") or ""),
                "size": int(value.get("size") or 0),
            }
        )
    return json.dumps(attachments, ensure_ascii=False)


def _bool_string(value: bool) -> str:
    return "true" if value else "false"


if __name__ == "__main__":
    raise SystemExit(main())
