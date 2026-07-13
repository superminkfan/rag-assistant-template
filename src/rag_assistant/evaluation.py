"""Deterministic retrieval evaluation for the bundled Ignite knowledge base."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rag_assistant.ports import Retriever


def load_evaluation_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("Evaluation cases must be a non-empty JSON array")
    ids: set[str] = set()
    for index, case in enumerate(data, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Evaluation case {index} must be an object")
        case_id = str(case.get("id") or "")
        query = str(case.get("query") or "")
        terms = case.get("expected_any_terms") or []
        if not case_id or not query or not isinstance(terms, list) or not terms:
            raise ValueError(f"Evaluation case {index} requires id, query, and expected_any_terms")
        if case_id in ids:
            raise ValueError(f"Duplicate evaluation case id: {case_id}")
        ids.add(case_id)
    return data


def evaluate_retrieval(
    cases: list[dict[str, Any]],
    *,
    retriever: Retriever,
    limit: int | None = None,
) -> dict[str, Any]:
    selected_cases = cases if limit is None else cases[:limit]
    results: list[dict[str, Any]] = []
    for case in selected_cases:
        documents = retriever.retrieve(str(case["query"]))
        searchable = "\n".join(
            f"{getattr(document, 'page_content', '')}\n"
            + " ".join(str(value) for value in (getattr(document, "metadata", {}) or {}).values())
            for document in documents
        ).casefold()
        components = {
            str((getattr(document, "metadata", {}) or {}).get("component") or "")
            for document in documents
        }
        source_types = {
            str((getattr(document, "metadata", {}) or {}).get("source_type") or "")
            for document in documents
        }
        expected_terms = [str(term).casefold() for term in case["expected_any_terms"]]
        expected_components = {str(value) for value in case.get("expected_components") or []}
        preferred_sources = {str(value) for value in case.get("preferred_source_types") or []}
        term_hit = any(term in searchable for term in expected_terms)
        component_hit = not expected_components or bool(components & expected_components)
        preferred_source_hit = not preferred_sources or bool(source_types & preferred_sources)
        citation_ready = bool(documents) and all(
            bool(
                (getattr(document, "metadata", {}) or {}).get("source_url")
                or (getattr(document, "metadata", {}) or {}).get("source")
                or (getattr(document, "metadata", {}) or {}).get("source_path")
            )
            for document in documents
        )
        results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "documents": len(documents),
                "term_hit": term_hit,
                "component_hit": component_hit,
                "preferred_source_hit": preferred_source_hit,
                "citation_ready": citation_ready,
                "source_types": sorted(source_types - {""}),
            }
        )

    count = len(results)
    return {
        "cases": count,
        "term_recall": _ratio(results, "term_hit"),
        "component_recall": _ratio(results, "component_hit"),
        "preferred_source_recall": _ratio(results, "preferred_source_hit"),
        "citation_readiness": _ratio(results, "citation_ready"),
        "failures": [result for result in results if not result["term_hit"] or not result["component_hit"]],
        "results": results,
    }


def format_evaluation_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"Cases: {summary['cases']}",
        f"Expected-term recall: {summary['term_recall']:.1%}",
        f"Component recall: {summary['component_recall']:.1%}",
        f"Preferred-source recall: {summary['preferred_source_recall']:.1%}",
        f"Citation readiness: {summary['citation_readiness']:.1%}",
    ]
    failures = summary.get("failures") or []
    if failures:
        lines.append("Failures:")
        lines.extend(
            f"- {failure['id']}: {failure['query']} (sources: {', '.join(failure['source_types']) or 'none'})"
            for failure in failures
        )
    return "\n".join(lines)


def _ratio(results: list[dict[str, Any]], key: str) -> float:
    if not results:
        return 0.0
    return sum(bool(result[key]) for result in results) / len(results)
