from dataclasses import dataclass, field
import json

import pytest

from rag_assistant.evaluation import (
    evaluate_retrieval,
    format_evaluation_summary,
    load_evaluation_cases,
)


@dataclass
class Doc:
    page_content: str
    metadata: dict = field(default_factory=dict)


class Retriever:
    def retrieve(self, query, *, limit=None):
        return [
            Doc(
                "WAL checkpoint and storage latency",
                {
                    "component": "persistence",
                    "source_type": "ignite-firefighter-tree",
                    "source": "tree.yaml",
                },
            )
        ]


def test_load_and_evaluate_retrieval_cases(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "wal",
                    "query": "WAL issue",
                    "expected_any_terms": ["checkpoint"],
                    "expected_components": ["persistence"],
                    "preferred_source_types": ["ignite-firefighter-tree"],
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_evaluation_cases(path)
    summary = evaluate_retrieval(cases, retriever=Retriever())

    assert summary["term_recall"] == 1.0
    assert summary["component_recall"] == 1.0
    assert summary["preferred_source_recall"] == 1.0
    assert summary["citation_readiness"] == 1.0
    assert "Expected-term recall: 100.0%" in format_evaluation_summary(summary)


def test_load_evaluation_cases_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "cases.json"
    case = {"id": "same", "query": "q", "expected_any_terms": ["x"]}
    path.write_text(json.dumps([case, case]), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate"):
        load_evaluation_cases(path)
