"""Provider-independent RAG application scenarios."""

from __future__ import annotations

import re

from rag_assistant.ports import LLM, RagDocument, Retriever


def ask(
    question: str,
    *,
    llm: LLM,
    retriever: Retriever,
) -> str:
    """Answer a documentation question using local RAG."""

    context_documents = retrieve_context(question, retriever=retriever)
    if not context_documents:
        return "Не нашел релевантных источников в локальной базе."

    prompt = build_qa_prompt(question, context_documents)
    response = llm.generate(prompt)
    return append_sources(response, context_documents)


def analyze_incident(
    incident_text: str,
    *,
    llm: LLM,
    retriever: Retriever,
) -> str:
    """Analyze an incident report against the local knowledge base."""

    retrieval_query = incident_text[:4000]
    context_documents = retrieve_context(retrieval_query, retriever=retriever)
    if not context_documents:
        return "Не нашел релевантных источников в локальной базе."

    prompt = build_incident_prompt(incident_text, context_documents)
    response = llm.generate(prompt)
    response = normalize_incident_report_headings(response)
    response = ensure_incident_section_citations(response, context_documents)
    return append_sources(response, context_documents)


def retrieve_context(
    query: str,
    *,
    retriever: Retriever,
) -> list[RagDocument]:
    """Retrieve context through the configured application port."""

    documents = retriever.retrieve(query)
    add_citation_metadata(documents)
    return documents


def build_qa_prompt(question: str, documents: list[RagDocument]) -> str:
    """Build the question-answering prompt."""

    return f"""Ты локальный RAG-ассистент по Ignite/DataGrid.
Отвечай только по контексту. Если контекста недостаточно, прямо скажи, чего не хватает.
Подкрепляй важные утверждения ссылками вида [1], [2].
При конфликте источников используй порядок доверия: официальная документация,
curated troubleshooting, внутренние incident cases, community Q&A, mailing list.
Для community-источников учитывай дату, версию продукта, score и accepted status.

Контекст:
{format_context(documents)}

Вопрос:
{question}

Ответь кратко, технически и с проверяемыми шагами там, где это уместно.
"""


def build_incident_prompt(incident_text: str, documents: list[RagDocument]) -> str:
    """Build the incident-analysis prompt."""

    return f"""Ты инженер поддержки Ignite/DataGrid и анализируешь инцидент.
Используй только приведенный контекст и текст инцидента. Не выдумывай факты.
Если данных недостаточно, явно перечисли, какие логи, метрики или команды нужны.
Не называй вывод уверенным, если он основан только на похожих прошлых инцидентах.
При конфликте предпочитай официальную документацию и version-compatible curated материалы;
community Q&A и mailing list используй как гипотезы или практические аналоги.
Каждый пункт в Evidence, Diagnostics и Mitigation должен заканчиваться ссылкой на источник вида [1] или [2].
Если для пункта нет источника, напиши, что это гипотеза и какие данные нужны для проверки.

Контекст:
{format_context(documents)}

Инцидент:
{incident_text}

Верни ответ строго в таком формате:

Summary
Likely Cause
Evidence
Diagnostics
Mitigation
Risk / Caveats
Confidence

В каждом разделе, где есть утверждения из документации, ставь ссылки [1], [2].
"""


def format_context(documents: list[RagDocument]) -> str:
    """Format retrieved documents with citation ids."""

    blocks: list[str] = []
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        source_id = metadata.get("source_id", "?")
        source = (
            metadata.get("source_url")
            or metadata.get("source")
            or metadata.get("source_path")
            or "unknown"
        )
        title = metadata.get("title") or ""
        section = metadata.get("section") or ""
        prefix = f"[{source_id}] Source: {source}"
        if title:
            prefix += f"\nTitle: {title}"
        if section:
            prefix += f"\nSection: {section}"
        if metadata.get("trust_tier"):
            prefix += f"\nTrust tier: {metadata['trust_tier']}"
        if metadata.get("product_version"):
            prefix += f"\nProduct version: {metadata['product_version']}"
        if metadata.get("published_at"):
            prefix += f"\nPublished: {metadata['published_at']}"
        blocks.append(f"{prefix}\n{getattr(document, 'page_content', '')}")
    return "\n\n---\n\n".join(blocks)


def add_citation_metadata(documents: list[RagDocument]) -> None:
    """Attach citation numbers to retrieved documents."""

    for index, document in enumerate(documents, start=1):
        metadata = getattr(document, "metadata", None)
        if metadata is None:
            if not hasattr(document, "__dict__"):
                continue
            metadata = {}
            setattr(document, "metadata", metadata)
        metadata["source_id"] = str(index)


def append_sources(response: str, documents: list[RagDocument]) -> str:
    """Append a deterministic source legend."""

    grouped: dict[tuple[str, str, str, str, str], list[str]] = {}
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        source_id = str(metadata.get("source_id") or "")
        source = str(
            metadata.get("source_url")
            or metadata.get("source")
            or metadata.get("source_path")
            or ""
        )
        title = str(metadata.get("title") or "")
        author = str(metadata.get("author") or "")
        license_name = str(metadata.get("license") or "")
        trust_tier = str(metadata.get("trust_tier") or "")
        if not source_id or not source:
            continue
        grouped.setdefault((source, title, author, license_name, trust_tier), []).append(source_id)

    lines: list[str] = []
    for (source, title, author, license_name, trust_tier), source_ids in grouped.items():
        citations = ", ".join(f"[{source_id}]" for source_id in source_ids)
        label = f"{citations} {source}"
        if title:
            label += f" - {title}"
        details = []
        if author:
            details.append(f"author: {author}")
        if trust_tier:
            details.append(f"trust: {trust_tier}")
        if license_name:
            details.append(f"license: {license_name}")
        if details:
            label += " (" + ", ".join(details) + ")"
        lines.append(label)
    if not lines:
        return response
    return f"{response.rstrip()}\n\nSources:\n" + "\n".join(lines)


def ensure_incident_section_citations(response: str, documents: list[RagDocument]) -> str:
    """Mark uncited operational bullets without attaching a misleading source."""

    target_sections = {"evidence", "diagnostics", "mitigation"}
    current_section = ""
    output_lines: list[str] = []

    for line in response.splitlines():
        section_name = _normalized_heading(line)
        if section_name:
            current_section = section_name
            output_lines.append(line)
            continue

        if current_section in target_sections and _is_bullet_line(line) and not _has_citation(line):
            output_lines.append(f"{line.rstrip()} [источник не указан]")
        else:
            output_lines.append(line)

    return "\n".join(output_lines)


def normalize_incident_report_headings(response: str) -> str:
    """Normalize common LLM heading drift in incident reports."""

    output_lines: list[str] = []
    previous_was_heading = False

    for line in response.splitlines():
        heading = _canonical_incident_heading(line)
        if heading:
            output_lines.append(heading)
            previous_was_heading = True
            continue

        if previous_was_heading and re.match(r"^\s*-{3,}\s*$", line):
            continue

        output_lines.append(line)
        previous_was_heading = False

    return "\n".join(output_lines)


def _first_source_id(documents: list[object]) -> str:
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        source_id = str(metadata.get("source_id") or "")
        if source_id:
            return source_id
    return ""


def _normalized_heading(line: str) -> str:
    cleaned = line.strip().strip("*# ").strip().lower()
    return cleaned if cleaned in {"summary", "likely cause", "evidence", "diagnostics", "mitigation", "risk / caveats", "confidence"} else ""


def _canonical_incident_heading(line: str) -> str:
    cleaned = line.strip().strip("*# ").strip()
    lowered = cleaned.lower()

    heading_aliases = {
        "Summary": ("summary", "сум"),
        "Likely Cause": ("likely cause",),
        "Evidence": ("evidence",),
        "Diagnostics": ("diagnostics",),
        "Mitigation": ("mitigation",),
        "Risk / Caveats": ("risk / caveats", "risk", "caveats"),
        "Confidence": ("confidence",),
    }
    for canonical, aliases in heading_aliases.items():
        if lowered in aliases or any(lowered.startswith(alias + " ") or lowered.startswith(alias) for alias in aliases):
            return canonical
    return ""


def _is_bullet_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(("- ", "* ")) or bool(re.match(r"^\d+\.\s+", stripped))


def _has_citation(line: str) -> bool:
    return bool(re.search(r"\[\d+\]", line))
