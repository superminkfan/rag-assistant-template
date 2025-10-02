"""Utilities for exporting Jira tickets with generated summaries."""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM


# Ensure the project root is importable when executing as a script.
CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from providers.ollama import DEFAULT_TEMPERATURE, OLLAMA_TEMPERATURE_ENV  # noqa: E402
from scripts.jira import tiket_saver as base  # noqa: E402


SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Summarize Jira issues for reporting. Provide concise overviews of the description and the discussion in the comments.",
        ),
        (
            "human",
            (
                "Issue Key: {key}\n"
                "Title: {title}\n"
                "Original Summary: {summary}\n"
                "Description:\n{description}\n\n"
                "Comments:\n{comments}\n\n"
                "Return a JSON object with keys 'description_summary' and 'comment_summary'.\n"
                "Each summary should be 1-3 sentences, objective, and ready for management reporting."
            ),
        ),
    ]
)


def _resolve_temperature() -> float:
    """Load the Ollama temperature from the configured environment variable."""

    raw_value = os.getenv(OLLAMA_TEMPERATURE_ENV)
    if raw_value is None or raw_value == "":
        return DEFAULT_TEMPERATURE

    try:
        return float(raw_value)
    except ValueError:
        return DEFAULT_TEMPERATURE


def _build_llm() -> OllamaLLM:
    """Instantiate the Ollama LLM configured for summaries."""

    temperature = _resolve_temperature()
    return OllamaLLM(model="llama3.2:latest", temperature=temperature)


def _format_comments(comments: Iterable[Dict[str, Any]]) -> str:
    """Create a readable representation of comments for prompting."""

    comment_list = list(comments)
    if not comment_list:
        return "No comments available."

    formatted: List[str] = []
    for idx, comment in enumerate(comment_list, start=1):
        author = comment.get("author") or "Unknown author"
        created = comment.get("created") or "Unknown date"
        body = comment.get("body") or ""
        formatted.append(f"{idx}. {author} ({created}):\n{body}")
    return "\n\n".join(formatted)


def _summarize_issue(
    llm: OllamaLLM,
    *,
    key: str,
    title: str,
    summary: str,
    description: str,
    comments: List[Dict[str, Any]],
) -> Tuple[str, str]:
    """Generate description and comment summaries for a Jira issue."""

    prompt_value = SUMMARY_PROMPT.format_prompt(
        key=key,
        title=title,
        summary=summary,
        description=description or "No description provided.",
        comments=_format_comments(comments),
    ).to_string()

    response = llm.invoke(prompt_value)

    description_summary: str | None = None
    comment_summary: str | None = None

    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        description_summary = parsed.get("description_summary")
        comment_summary = parsed.get("comment_summary")

    if not description_summary:
        description_summary = description or ""
    if not comment_summary:
        comment_summary = _format_comments(comments)

    return description_summary.strip(), comment_summary.strip()


def collect_summarized_issues(
    session: Any,
    jql: str,
    *,
    limit: int,
    llm: OllamaLLM,
) -> List[Dict[str, str]]:
    """Fetch, filter, and summarize Jira issues for export."""

    gathered: List[Dict[str, str]] = []
    start = 0
    page_size = 100

    while len(gathered) < limit:
        keys = base.search_issue_keys(session, jql, start_at=start, max_results=page_size)
        if not keys:
            break

        for issue_key in keys:
            basic = base.get_issue_basic(session, issue_key)
            title = basic["summary"]
            if not base.title_has_support_tag(title):
                continue

            comments = base.get_issue_comments(session, issue_key)
            description_summary, comment_summary = _summarize_issue(
                llm,
                key=basic["key"],
                title=title,
                summary=title,
                description=basic.get("description") or "",
                comments=comments,
            )

            gathered.append(
                {
                    "Идентификатор ISE": basic["key"],
                    "Название": title,
                    "Описание": description_summary,
                    "Комментарии": comment_summary,
                }
            )

            if len(gathered) >= limit:
                break

        start += page_size

    return gathered


def save_rows_to_csv(rows: List[Dict[str, str]], path: str = base.OUTPUT_CSV) -> str:
    """Persist the summarized issues to CSV using the base schema."""

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["Идентификатор ISE", "Название", "Описание", "Комментарии"]

    with open(path, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return path


if __name__ == "__main__":
    session = base.get_session()
    llm = _build_llm()
    rows = collect_summarized_issues(
        session,
        base.DEFAULT_JQL,
        limit=base.MAX_RESULTS,
        llm=llm,
    )

    print(
        "Отфильтровано задач: "
        f"{len(rows)} (по шаблону названия [SBTSUPPORT-<num>] и сгенерированными сводками)"
    )
    output_path = save_rows_to_csv(rows, base.OUTPUT_CSV)
    print(f"Сохранено в: {output_path}")
