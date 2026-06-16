from __future__ import annotations

import csv

import pytest

from rag_assistant.docs import load_jira_snapshot_source
from rag_assistant.indexing import build_chunks
from scripts.jira.export_support_tickets import (
    COMMENT_COLUMNS,
    ISSUE_COLUMNS,
    build_snapshot_rows,
)
from tests.test_jira_export import make_comment, make_issue


def test_load_jira_snapshot_creates_issue_and_comment_documents(tmp_path):
    issue_row, comments = build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-123] JVM memory issue"),
        [make_comment("10", body="os::commit_memory failed during analysis")],
        base_url="https://jira.example",
    )
    write_variant(tmp_path, [issue_row], comments)

    documents = load_jira_snapshot_source(tmp_path)

    assert len(documents) == 2
    issue_document, comment_document = documents
    assert issue_document.metadata["source"] == "jira://issue/ISE-1"
    assert issue_document.metadata["record_type"] == "issue"
    assert comment_document.metadata["source"] == "jira://issue/ISE-1/comment/10"
    assert comment_document.metadata["record_type"] == "comment"
    assert comment_document.metadata["author"] == "Engineer"
    assert comment_document.metadata["component"] == "persistence"


def test_jira_comment_chunks_repeat_issue_and_author_context(tmp_path):
    long_body = "checkpoint WAL technical evidence " * 100
    issue_row, comments = build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-123] Persistence incident"),
        [make_comment("10", body=long_body)],
        base_url="https://jira.example",
    )
    write_variant(tmp_path, [issue_row], comments)
    documents = load_jira_snapshot_source(tmp_path)

    chunks, _ = build_chunks(documents, chunk_size=300, chunk_overlap=40)
    comment_chunks = [
        chunk for chunk in chunks if chunk.metadata["record_type"] == "comment"
    ]

    assert len(comment_chunks) > 2
    for chunk in comment_chunks:
        assert "Issue Key: ISE-1" in chunk.page_content
        assert "Title: [SBTSUPPORT-123] Persistence incident" in chunk.page_content
        assert "Author: Engineer" in chunk.page_content
        assert "Comment ID: 10" in chunk.page_content


def test_jira_snapshot_chunk_ids_do_not_depend_on_csv_row_order(tmp_path):
    first_issue, first_comments = build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-1] First"),
        [make_comment("10")],
        base_url="https://jira.example",
    )
    second_issue, second_comments = build_snapshot_rows(
        make_issue("ISE-2", "[SBTSUPPORT-2] Second"),
        [make_comment("20")],
        base_url="https://jira.example",
    )
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    write_variant(
        first_dir,
        [first_issue, second_issue],
        first_comments + second_comments,
    )
    write_variant(
        second_dir,
        [second_issue, first_issue],
        second_comments + first_comments,
    )

    first_chunks, first_ids = build_chunks(load_jira_snapshot_source(first_dir))
    second_chunks, second_ids = build_chunks(load_jira_snapshot_source(second_dir))
    first_mapping = {
        (chunk.metadata["source"], chunk.metadata["chunk_index"]): chunk_id
        for chunk, chunk_id in zip(first_chunks, first_ids)
    }
    second_mapping = {
        (chunk.metadata["source"], chunk.metadata["chunk_index"]): chunk_id
        for chunk, chunk_id in zip(second_chunks, second_ids)
    }

    assert first_mapping == second_mapping


def test_jira_snapshot_rejects_orphan_comments(tmp_path):
    issue_row, comments = build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-1] Incident"),
        [make_comment("10")],
        base_url="https://jira.example",
    )
    comments[0]["issue_key"] = "ISE-404"
    write_variant(tmp_path, [issue_row], comments)

    with pytest.raises(ValueError, match="orphan comment"):
        load_jira_snapshot_source(tmp_path)


def test_jira_snapshot_supports_multiline_comment_over_100kb(tmp_path):
    body = ("line with evidence\n" * 7000) + "done"
    issue_row, comments = build_snapshot_rows(
        make_issue("ISE-1", "[SBTSUPPORT-1] Large incident"),
        [make_comment("10", body=body)],
        base_url="https://jira.example",
    )
    write_variant(tmp_path, [issue_row], comments)

    documents = load_jira_snapshot_source(tmp_path)

    comment = next(doc for doc in documents if doc.metadata["record_type"] == "comment")
    assert comment.page_content == body
    assert len(comment.page_content) > 100_000


def write_variant(path, issues, comments):
    path.mkdir(parents=True, exist_ok=True)
    with (path / "issues.csv").open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=ISSUE_COLUMNS)
        writer.writeheader()
        writer.writerows(issues)
    with (path / "comments.csv").open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=COMMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(comments)
