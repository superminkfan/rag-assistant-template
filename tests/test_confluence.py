from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from rag_assistant import confluence
from rag_assistant.docs import load_confluence_snapshot_source


def test_html_fragment_to_markdown_preserves_structure_and_removes_chrome():
    html = """
<div id="main-content">
  <div class="noprint">Edit page</div>
  <h2>Checkpoint</h2>
  <p>Use <strong>WAL</strong><br>carefully.</p>
  <ul><li>First</li><li>Second</li></ul>
  <table><tr><th>Name</th><th>Value</th></tr><tr><td>mode</td><td>LOG_ONLY</td></tr></table>
  <pre><code class="language-java">ignite.cluster().state(ACTIVE);</code></pre>
  <img alt="Architecture" src="/download/diagram.png">
  <script>secretUiCode()</script>
</div>
"""

    text = confluence.html_fragment_to_markdown(
        html,
        base_url="https://wiki.example/confluence/page",
    )

    assert "## Checkpoint" in text
    assert "**WAL**" in text
    assert "- First" in text
    assert "| Name | Value |" in text
    assert "```java" in text
    assert "Image: Architecture (https://wiki.example/download/diagram.png)" in text
    assert "Edit page" not in text
    assert "secretUiCode" not in text


def test_parse_offline_html_extracts_metadata_and_main_content():
    page = confluence.parse_offline_html(
        saved_html("1099939602", "Idle verify", "<h2>Details</h2><p>Technical content " + "x" * 40 + "</p>"),
        source_id="sberworks",
    )

    assert page["metadata"]["source_id"] == "sberworks"
    assert page["metadata"]["confluence_page_id"] == "1099939602"
    assert page["metadata"]["space_key"] == "ISE"
    assert page["metadata"]["source_url"].endswith("pageId=1099939602")
    assert "## Details" in page["page_content"]
    assert "Navigation text" not in page["page_content"]


def test_collect_offline_pages_requires_all_five_sberworks_pages(tmp_path):
    for page_id in sorted(confluence.EXPECTED_SBER_PAGE_IDS):
        (tmp_path / f"{page_id}.html").write_text(
            saved_html(page_id, f"Page {page_id}", "<p>" + "content " * 10 + "</p>"),
            encoding="utf-8",
        )
    (tmp_path / "unrelated.html").write_text("<html>not confluence</html>", encoding="utf-8")

    pages = confluence.collect_offline_pages(tmp_path, source_id="sberworks")

    assert len(pages) == 5
    assert {page["metadata"]["confluence_page_id"] for page in pages} == (
        confluence.EXPECTED_SBER_PAGE_IDS
    )

    (tmp_path / "912792424.html").unlink()
    with pytest.raises(ValueError, match="912792424"):
        confluence.collect_offline_pages(tmp_path, source_id="sberworks")


def test_extract_direct_page_links_filters_deduplicates_and_does_not_recurse():
    text = """
[Persistence](https://cwiki.apache.org/confluence/display/IGNITE/Persistence)
[Duplicate](https://cwiki.apache.org/confluence/display/IGNITE/Persistence#section)
[By id](/confluence/pages/viewpage.action?pageId=42)
[Other space](https://cwiki.apache.org/confluence/display/OTHER/Nope)
[External](https://example.com/confluence/display/IGNITE/Nope)
"""

    links = confluence.extract_direct_page_links(
        text,
        base_url=confluence.DEFAULT_APACHE_SEED_URL,
        allowed_host="cwiki.apache.org",
        space_key="IGNITE",
    )

    assert links == [
        "https://cwiki.apache.org/confluence/display/IGNITE/Persistence",
        "https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=42",
    ]


def test_collect_public_pages_uses_rest_and_only_seed_links():
    session = FakeRestSession(
        [
            rest_payload(
                "1",
                "Design Documents",
                '<p><a href="/confluence/display/IGNITE/Persistence">Persistence</a></p>'
                '<p><a href="https://example.com/nope">External</a></p>',
            ),
            '<div id="main-content">'
            '<a href="/confluence/display/IGNITE/Persistence">Persistence</a>'
            '<a href="https://example.com/nope">External</a>'
            '</div>',
            rest_payload("2", "Persistence", "<h2>WAL</h2><p>" + "details " * 8 + "</p>"),
        ]
    )

    pages = confluence.collect_public_pages(
        session,
        source_id="apache-ignite-design",
    )

    assert [page["metadata"]["confluence_page_id"] for page in pages] == ["1", "2"]
    assert [page["metadata"]["crawl_depth"] for page in pages] == [0, 1]
    assert len(session.calls) == 3
    assert "rest/api/content" in session.calls[0][0]
    assert session.calls[1][0] == confluence.DEFAULT_APACHE_SEED_URL
    assert "rest/api/content" in session.calls[2][0]


def test_snapshot_is_atomic_validated_and_loadable(tmp_path, monkeypatch):
    pages = [
        confluence.parse_offline_html(
            saved_html("1", "Persistence WAL", "<h2>Checkpoint</h2><p>" + "details " * 8 + "</p>"),
            source_id="test-source",
        )
    ]
    generated_at = datetime(2026, 6, 24, 1, 2, 3, tzinfo=timezone.utc)
    first = confluence.write_snapshot(
        output_root=tmp_path,
        source_id="test-source",
        pages=pages,
        mode="offline-html",
        generated_at=generated_at,
    )
    latest_before = (tmp_path / "test-source/latest").resolve()
    manifest, stored_pages = confluence.validate_snapshot(first)
    documents = load_confluence_snapshot_source(first)

    assert manifest["counts"] == {"pages": 1}
    assert stored_pages == pages
    assert documents[0].metadata["component"] == "persistence"
    assert documents[0].metadata["guide"] == "ISE"

    monkeypatch.setattr(confluence, "validate_snapshot", lambda path: (_ for _ in ()).throw(ValueError("bad")))
    with pytest.raises(ValueError, match="bad"):
        confluence.write_snapshot(
            output_root=tmp_path,
            source_id="test-source",
            pages=pages,
            mode="offline-html",
            generated_at=generated_at,
        )
    assert (tmp_path / "test-source/latest").resolve() == latest_before
    assert not list((tmp_path / "test-source/snapshots").glob(".tmp-*"))


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload)

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeRestSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def get(self, url, *, params=None, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse(self.payloads.pop(0))


def rest_payload(page_id, title, body):
    return {
        "results": [
            {
                "id": page_id,
                "title": title,
                "space": {"key": "IGNITE"},
                "body": {"view": {"value": body}},
                "version": {"number": 2, "when": "2026-01-01T00:00:00Z"},
            }
        ]
    }


def saved_html(page_id, title, body):
    return f"""<!doctype html>
<html><head>
<meta name="confluence-base-url" content="https://sberworks.ru/wiki">
<meta name="ajs-page-title" content="{title}">
<meta name="ajs-page-id" content="{page_id}">
<meta name="ajs-space-key" content="ISE">
<meta name="ajs-page-version-number" content="3">
</head><body><nav>Navigation text</nav><div id="main-content">{body}</div></body></html>"""
