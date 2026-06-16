from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from scripts.jira import export_support_tickets as exporter


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse(self.payloads.pop(0))


def test_iter_matching_issues_paginates_and_filters_strict_prefix():
    session = FakeSession(
        [
            {
                "total": 3,
                "issues": [
                    make_issue("ISE-1", "[SBTSUPPORT-1] Match"),
                    make_issue("ISE-2", " Prefix [SBTSUPPORT-2] No match"),
                ],
            },
            {
                "total": 3,
                "issues": [make_issue("ISE-3", "[SBTSUPPORT-3] Match")],
            },
        ]
    )

    issues = list(
        exporter.iter_matching_issues(
            session,
            base_url="https://jira.example",
            jql="project = ISE",
            page_size=2,
        )
    )

    assert [issue["key"] for issue in issues] == ["ISE-1", "ISE-3"]
    assert [call[1]["startAt"] for call in session.calls] == [0, 2]


def test_fetch_all_comments_reads_every_page():
    session = FakeSession(
        [
            {"total": 3, "comments": [make_comment("1"), make_comment("2")]},
            {"total": 3, "comments": [make_comment("3")]},
        ]
    )

    comments = exporter.fetch_all_comments(
        session,
        base_url="https://jira.example",
        issue_key="ISE-1",
        page_size=2,
    )

    assert [comment["id"] for comment in comments] == ["1", "2", "3"]
    assert [call[1]["startAt"] for call in session.calls] == [0, 2]


def test_build_session_configures_transient_http_retries(tmp_path, monkeypatch):
    cert_path = tmp_path / "cert.pem"
    cert_path.write_text("certificate", encoding="utf-8")
    monkeypatch.setenv("RAG_ASSISTANT_JIRA_USERNAME", "user")
    monkeypatch.setenv("RAG_ASSISTANT_JIRA_PASSWORD", "secret")

    session = exporter.build_session(cert_path=cert_path)
    retry = session.get_adapter("https://").max_retries

    assert session.auth == ("user", "secret")
    assert retry.total == 5
    assert retry.backoff_factor == 0.5
    assert {429, 500, 502, 503, 504} <= set(retry.status_forcelist)


def test_build_session_requires_env_credentials(tmp_path, monkeypatch):
    cert_path = tmp_path / "cert.pem"
    cert_path.write_text("certificate", encoding="utf-8")
    monkeypatch.delenv("RAG_ASSISTANT_JIRA_USERNAME", raising=False)
    monkeypatch.delenv("RAG_ASSISTANT_JIRA_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="RAG_ASSISTANT_JIRA_USERNAME"):
        exporter.build_session(cert_path=cert_path)


def test_collect_snapshot_rows_honors_limit(monkeypatch):
    issues = [
        make_issue("ISE-1", "[SBTSUPPORT-1] First"),
        make_issue("ISE-2", "[SBTSUPPORT-2] Second"),
        make_issue("ISE-3", "[SBTSUPPORT-3] Third"),
    ]
    monkeypatch.setattr(exporter, "iter_matching_issues", lambda *args, **kwargs: iter(issues))
    monkeypatch.setattr(
        exporter,
        "fetch_all_comments",
        lambda *args, **kwargs: [make_comment(f"{kwargs['issue_key']}-1")],
    )

    issue_rows, comment_rows = exporter.collect_snapshot_rows(
        object(),
        base_url="https://jira.example",
        jql="project = ISE",
        limit=2,
    )

    assert [row["issue_key"] for row in issue_rows] == ["ISE-1", "ISE-2"]
    assert [row["issue_key"] for row in comment_rows] == ["ISE-1", "ISE-2"]


def test_export_parser_supports_limit():
    args = exporter.build_parser().parse_args(["--limit", "3"])

    assert args.limit == 3


def test_export_main_uses_config_and_cli_overrides(tmp_path, monkeypatch, capsys):
    cert_path = tmp_path / "client.pem"
    cert_path.write_text("certificate", encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
jira:
  base_url: https://jira.example
  jql: project = CONFIG
  cert_path: {cert_path}
  output_root: config-output
""",
        encoding="utf-8",
    )
    session = object()
    calls = {}

    def fake_build_session(**kwargs):
        calls["session"] = kwargs
        return session

    def fake_export_snapshot(session_arg, **kwargs):
        calls["export_session"] = session_arg
        calls["export"] = kwargs
        return tmp_path / "published"

    monkeypatch.setenv("RAG_ASSISTANT_JIRA_USERNAME", "user")
    monkeypatch.setenv("RAG_ASSISTANT_JIRA_PASSWORD", "secret")
    monkeypatch.setattr(exporter, "build_session", fake_build_session)
    monkeypatch.setattr(exporter, "export_snapshot", fake_export_snapshot)

    result = exporter.main(
        [
            "--config",
            str(config_path),
            "--jql",
            "project = CLI",
            "--limit",
            "2",
        ]
    )

    assert result == 0
    assert calls["session"] == {"cert_path": cert_path}
    assert calls["export_session"] is session
    assert calls["export"]["base_url"] == "https://jira.example"
    assert calls["export"]["jql"] == "project = CLI"
    assert calls["export"]["output_root"] == (tmp_path / "config-output").resolve()
    assert calls["export"]["limit"] == 2
    assert "Published Jira snapshot" in capsys.readouterr().out


def test_redact_secrets_preserves_normal_technical_text():
    source = """Authorization: Bearer abc.def.ghi
password = super-secret
"client_secret": "quoted-value"
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature
-----BEGIN RSA PRIVATE KEY-----
private material
-----END RSA PRIVATE KEY-----
WAL checkpoint failed at 10.0.0.1; token count is 42.
"""

    redacted, count = exporter.redact_secrets(source)

    assert count == 5
    assert "super-secret" not in redacted
    assert "quoted-value" not in redacted
    assert "private material" not in redacted
    assert "WAL checkpoint failed at 10.0.0.1; token count is 42." in redacted


def test_substantive_comment_threshold_is_30_non_whitespace_chars():
    assert not exporter.is_substantive_comment("a " * 29)
    assert exporter.is_substantive_comment("a " * 30)


@pytest.mark.parametrize(
    ("description", "comment_body", "status", "resolution", "expected"),
    [
        ("Client report", "x" * 30, "Выполнен", "", True),
        ("", "x" * 30, "Выполнен", "Исправлен", False),
        ("Client report", "x" * 29, "Выполнен", "Исправлен", False),
        ("Client report", "x" * 30, "Cancelled", "Исправлен", False),
        ("Client report", "x" * 30, "Отклонен исполнителем", "", False),
        ("Client report", "x" * 30, "Закрыт", "Дубликат", False),
        ("Client report", "x" * 30, "Закрыт", "Отклонен", False),
        ("Client report", "x" * 30, "Закрыт", "Неполный", False),
    ],
)
def test_curated_eligibility_rules(
    description,
    comment_body,
    status,
    resolution,
    expected,
):
    issue = make_issue(
        "ISE-1",
        "[SBTSUPPORT-1] Incident",
        description=description,
        status=status,
        resolution=resolution,
    )
    issue_row, _ = exporter.build_snapshot_rows(
        issue,
        [make_comment("10", body=comment_body)],
        base_url="https://jira.example",
    )

    assert (issue_row["curated_eligible"] == "true") is expected
    if not resolution:
        assert "missing_resolution" in json.loads(issue_row["quality_flags_json"])


def test_write_snapshot_publishes_latest_and_keeps_it_on_failure(tmp_path, monkeypatch):
    issue_row, comments = exporter.build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-1] Incident", description="Client report"),
        [make_comment("10", body="technical analysis " * 3)],
        base_url="https://jira.example",
    )
    generated_at = datetime(2026, 6, 15, 1, 2, 3, tzinfo=timezone.utc)
    first = exporter.write_snapshot(
        output_root=tmp_path,
        issue_rows=[issue_row],
        comment_rows=comments,
        base_url="https://jira.example",
        jql="project = ISE",
        generated_at=generated_at,
    )
    latest_before = (tmp_path / "latest").resolve()

    def fail_write(*args, **kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr(exporter, "_write_csv", fail_write)
    with pytest.raises(OSError, match="disk failure"):
        exporter.write_snapshot(
            output_root=tmp_path,
            issue_rows=[issue_row],
            comment_rows=comments,
            base_url="https://jira.example",
            jql="project = ISE",
            generated_at=generated_at,
        )

    assert first == latest_before
    assert (tmp_path / "latest").resolve() == latest_before
    assert not list((tmp_path / "snapshots").glob(".tmp-*"))


def test_write_snapshot_validates_comment_fields_larger_than_default_csv_limit(tmp_path):
    issue_row, comments = exporter.build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-1] Large comment", description="Client report"),
        [make_comment("10", body="large evidence\n" * 12_000)],
        base_url="https://jira.example",
    )

    snapshot_dir = exporter.write_snapshot(
        output_root=tmp_path,
        issue_rows=[issue_row],
        comment_rows=comments,
        base_url="https://jira.example",
        jql="project = ISE",
        generated_at=datetime(2026, 6, 15, 2, 0, 0, tzinfo=timezone.utc),
    )

    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["counts"]["full_comments"] == 1


def make_issue(
    issue_key,
    summary,
    *,
    description="Description",
    status="Выполнен",
    resolution="Исправлен",
):
    return {
        "key": issue_key,
        "fields": {
            "summary": summary,
            "description": description,
            "status": {"name": status},
            "resolution": {"name": resolution} if resolution else None,
            "priority": {"name": "Medium"},
            "issuetype": {"name": "Incident"},
            "created": "2026-01-01T00:00:00.000+0000",
            "updated": "2026-01-02T00:00:00.000+0000",
            "resolutiondate": "",
            "components": [{"name": "Persistence"}],
            "labels": ["ignite"],
            "versions": [{"name": "18.0"}],
            "fixVersions": [],
            "attachment": [],
        },
    }


def make_comment(comment_id, *, body="Detailed technical analysis of the incident"):
    return {
        "id": comment_id,
        "author": {"displayName": "Engineer"},
        "created": "2026-01-01T01:00:00.000+0000",
        "updated": "2026-01-01T02:00:00.000+0000",
        "body": body,
    }
