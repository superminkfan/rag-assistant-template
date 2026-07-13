from __future__ import annotations

import gzip
import json
from pathlib import Path

from rag_assistant.docs import load_source_documents


BUNDLED_KB = Path(__file__).resolve().parents[1] / "data" / "ignite-firefighter"


def test_bundled_tree_expands_machine_readable_records():
    documents = load_source_documents(
        BUNDLED_KB,
        source_type="ignite-firefighter-tree",
    )

    assert len(documents) == 331
    record_types = {document.metadata["record_type"] for document in documents}
    assert record_types == {
        "provenance_source",
        "fact",
        "action",
        "decision_node",
        "checklist",
    }
    start = next(
        document
        for document in documents
        if document.metadata["record_id"] == "node:start"
    )
    assert "resolved_action" in start.page_content
    assert start.metadata["trust_tier"] == "curated"


def test_bundled_gc_note_has_collector_metadata():
    documents = load_source_documents(
        BUNDLED_KB,
        source_type="ignite-firefighter-notes",
    )

    assert len(documents) == 1
    assert documents[0].metadata["collector"] == "G1|Shenandoah|ZGC"
    assert "Allocation Stall" in documents[0].page_content


def test_stackoverflow_loader_keeps_question_response_context_and_quality(tmp_path):
    source = tmp_path / "stackoverflow"
    source.mkdir()
    record = {
        "source": "stackoverflow",
        "kind": "answered_question",
        "id": "42",
        "url": "https://stackoverflow.com/questions/42/example",
        "title": "Ignite 2.17 WAL failure",
        "created_at": "2025-01-01T00:00:00Z",
        "score": 3,
        "tags": ["ignite", "wal"],
        "body_format": "html",
        "question": {"body": "<p>Why does <code>WAL</code> fail?</p>"},
        "responses": [
            {
                "id": "84",
                "created_at": "2025-01-02T00:00:00Z",
                "score": 5,
                "is_accepted": True,
                "body": "<p>Inspect checkpoint logs.</p><pre><code>control.sh</code></pre>",
            }
        ],
    }
    (source / "answered-questions.combined.jsonl").write_text(
        json.dumps(record) + "\n", encoding="utf-8"
    )
    (source / "manifest.json").write_text(
        json.dumps({"records": 1}), encoding="utf-8"
    )

    documents = load_source_documents(tmp_path, source_type="stackoverflow-kb")

    assert len(documents) == 1
    document = documents[0]
    assert "## Question" in document.page_content
    assert "## Response" in document.page_content
    assert "control.sh" in document.page_content
    assert "<p>" not in document.page_content
    assert document.metadata["source_url"] == "https://stackoverflow.com/a/84"
    assert document.metadata["is_accepted"] is True
    assert document.metadata["product_version"] == "2.17"
    assert document.metadata["quality_score"] > 0.7


def test_mailing_list_loader_groups_subject_and_cleans_quotes(tmp_path):
    source = tmp_path / "mailing-list"
    source.mkdir()
    mbox = b"""From sender@example.com Thu Nov 01 00:00:00 2018
Message-Id: <one@example.com>
Subject: Re: WAL checkpoint latency
From: Alice <alice@example.com>
Date: Thu, 1 Nov 2018 00:00:00 +0000
Content-Type: text/plain; charset=utf-8

Checkpoint takes too long on Ignite 2.7 and storage latency is high.
> Previous message with private@example.com

From sender@example.com Thu Nov 01 00:01:00 2018
Message-Id: <two@example.com>
Subject: WAL checkpoint latency
From: Bob <bob@example.com>
Date: Thu, 1 Nov 2018 00:01:00 +0000
Content-Type: text/plain; charset=utf-8

Inspect WAL fsync and checkpoint duration before tuning.
"""
    (source / "answered_threads.mbox.gz").write_bytes(gzip.compress(mbox))
    (source / "manifest.json").write_text(
        json.dumps({"messages": 2}), encoding="utf-8"
    )

    documents = load_source_documents(
        tmp_path,
        source_type="ignite-user-mailing-list",
    )

    assert len(documents) == 2
    assert len({document.metadata["thread_id"] for document in documents}) == 1
    assert all("@example.com" not in document.page_content for document in documents)
    assert "Previous message" not in documents[0].page_content
    assert documents[0].metadata["product_version"] == "2.7"


def test_bundled_stackoverflow_and_mail_counts_match_curated_loaders():
    stackoverflow = load_source_documents(BUNDLED_KB, source_type="stackoverflow-kb")
    mailing_list = load_source_documents(
        BUNDLED_KB, source_type="ignite-user-mailing-list"
    )

    assert len(stackoverflow) == 2645
    assert len(mailing_list) == 499
