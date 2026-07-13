"""Create validated snapshots from public and offline Confluence pages."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Callable
from urllib.parse import parse_qs, unquote_plus, urljoin, urlparse
import uuid

from bs4 import BeautifulSoup, NavigableString, Tag
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


SCHEMA_VERSION = "1"
DEFAULT_APACHE_SEED_URL = (
    "https://cwiki.apache.org/confluence/display/IGNITE/Design+Documents"
)
EXPECTED_SBER_PAGE_IDS = {
    "912792424",
    "1062300594",
    "1085438720",
    "1099939602",
    "1224289762",
}
REQUEST_TIMEOUT_SECONDS = 60


def build_public_session() -> requests.Session:
    """Create a GET-only session with retries for public Confluence."""

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
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def parse_offline_html(
    html: str,
    *,
    source_id: str,
    fallback_url: str | None = None,
) -> dict[str, Any]:
    """Normalize one browser-saved Confluence HTML page."""

    soup = BeautifulSoup(html, "html.parser")
    page_id = _meta_content(soup, "ajs-page-id")
    title = _meta_content(soup, "ajs-page-title")
    space_key = _meta_content(soup, "ajs-space-key")
    base_url = _meta_content(soup, "confluence-base-url")
    version = _meta_content(soup, "ajs-page-version-number")
    if not page_id or not title or not space_key:
        raise ValueError("Saved HTML is missing Confluence page id, title, or space key")

    source_url = fallback_url or (
        f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={page_id}"
        if base_url
        else ""
    )
    if not source_url:
        raise ValueError(f"Cannot determine source URL for Confluence page {page_id}")

    content = soup.select_one("#main-content")
    if content is None:
        raise ValueError(f"Confluence page {page_id} has no #main-content element")
    markdown = html_fragment_to_markdown(str(content), base_url=source_url)
    if not _has_substantive_content(markdown):
        raise ValueError(f"Confluence page {page_id} has no substantive content")

    updated_at = ""
    modified = soup.select_one("a.last-modified")
    if modified is not None:
        updated_at = str(modified.get("aria-label") or modified.get_text(" ", strip=True))

    return _page_record(
        page_content=markdown,
        source_id=source_id,
        source_url=source_url,
        page_id=page_id,
        title=title,
        space_key=space_key,
        version=version,
        updated_at=updated_at,
        crawl_depth=0,
    )


def collect_offline_pages(input_dir: Path, *, source_id: str) -> list[dict[str, Any]]:
    """Read browser-saved pages without making any network requests."""

    input_dir = input_dir.expanduser().resolve()
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Offline Confluence directory not found: {input_dir}")

    by_page_id: dict[str, dict[str, Any]] = {}
    for html_path in sorted(input_dir.rglob("*.html")):
        try:
            page = parse_offline_html(
                html_path.read_text(encoding="utf-8", errors="replace"),
                source_id=source_id,
            )
        except ValueError:
            if source_id == "sberworks":
                continue
            raise
        page_id = str(page["metadata"]["confluence_page_id"])
        if source_id == "sberworks" and page_id not in EXPECTED_SBER_PAGE_IDS:
            continue
        if page_id in by_page_id:
            raise ValueError(f"Duplicate Confluence page id in offline export: {page_id}")
        by_page_id[page_id] = page

    if source_id == "sberworks":
        missing = EXPECTED_SBER_PAGE_IDS - set(by_page_id)
        if missing:
            raise ValueError(
                "Offline SberWorks export is missing page ids: "
                + ", ".join(sorted(missing))
            )
    if not by_page_id:
        raise ValueError(f"No valid Confluence HTML pages found in {input_dir}")
    return [by_page_id[key] for key in sorted(by_page_id)]


def collect_public_pages(
    session: requests.Session,
    *,
    source_id: str,
    seed_url: str = DEFAULT_APACHE_SEED_URL,
    allowed_host: str = "cwiki.apache.org",
    space_key: str = "IGNITE",
    progress: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    """Fetch a seed and its direct same-space links through Confluence REST."""

    seed = _fetch_rest_page(
        session,
        page_url=seed_url,
        source_id=source_id,
        expected_space=space_key,
        crawl_depth=0,
    )
    rendered_response = session.get(seed_url, timeout=REQUEST_TIMEOUT_SECONDS)
    rendered_response.raise_for_status()
    rendered_soup = BeautifulSoup(rendered_response.text, "html.parser")
    rendered_content = rendered_soup.select_one("#main-content")
    if rendered_content is None:
        raise ValueError(f"Confluence seed has no #main-content element: {seed_url}")
    links = extract_direct_page_links(
        str(rendered_content),
        base_url=seed_url,
        allowed_host=allowed_host,
        space_key=space_key,
    )
    if not links:
        raise ValueError(f"No direct Confluence page links found at {seed_url}")

    pages = [seed]
    seen_page_ids = {str(seed["metadata"]["confluence_page_id"])}
    for index, page_url in enumerate(links, start=1):
        page = _fetch_rest_page(
            session,
            page_url=page_url,
            source_id=source_id,
            expected_space=space_key,
            crawl_depth=1,
        )
        page_id = str(page["metadata"]["confluence_page_id"])
        if page_id not in seen_page_ids:
            pages.append(page)
            seen_page_ids.add(page_id)
        if progress:
            progress(f"Fetched {index}/{len(links)} linked Confluence pages.")
    return pages


def extract_direct_page_links(
    markdown_or_html: str,
    *,
    base_url: str,
    allowed_host: str,
    space_key: str,
) -> list[str]:
    """Return canonical direct same-space links in source order."""

    hrefs = re.findall(r"\[[^\]]*\]\(([^)]+)\)", markdown_or_html)
    if "<a " in markdown_or_html:
        hrefs.extend(
            str(anchor.get("href"))
            for anchor in BeautifulSoup(markdown_or_html, "html.parser").select("a[href]")
        )

    result: list[str] = []
    seen: set[str] = set()
    for href in hrefs:
        absolute = _canonical_url(urljoin(base_url, href))
        parsed = urlparse(absolute)
        display_prefix = f"/confluence/display/{space_key}/"
        is_page_id_url = parsed.path == "/confluence/pages/viewpage.action" and bool(
            parse_qs(parsed.query).get("pageId")
        )
        if (
            parsed.scheme == "https"
            and parsed.hostname == allowed_host
            and (parsed.path.startswith(display_prefix) or is_page_id_url)
            and absolute not in seen
        ):
            seen.add(absolute)
            result.append(absolute)
    return result


def html_fragment_to_markdown(fragment: str, *, base_url: str = "") -> str:
    """Convert the useful subset of rendered Confluence HTML to Markdown."""

    soup = BeautifulSoup(fragment, "html.parser")
    for unwanted in soup.select(
        "script, style, noscript, .noprint, .hidden, .plugin_attachments_container"
    ):
        unwanted.decompose()

    rendered = "".join(_render_node(node, base_url=base_url) for node in soup.contents)
    rendered = re.sub(r"[ \t]+\n", "\n", rendered)
    rendered = re.sub(r"\n[ \t]+", "\n", rendered)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    return rendered.strip() + "\n"


def write_snapshot(
    *,
    output_root: Path,
    source_id: str,
    pages: list[dict[str, Any]],
    mode: str,
    seed_url: str | None = None,
    generated_at: datetime | None = None,
) -> Path:
    """Write, validate, and atomically publish a Confluence snapshot."""

    if not pages:
        raise ValueError("Cannot publish an empty Confluence snapshot")
    generated_at = generated_at or datetime.now(timezone.utc)
    timestamp = generated_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    profile_root = output_root.expanduser().resolve() / source_id
    snapshots_root = profile_root / "snapshots"
    snapshots_root.mkdir(parents=True, exist_ok=True)
    final_dir = snapshots_root / timestamp
    if final_dir.exists():
        final_dir = snapshots_root / f"{timestamp}-{uuid.uuid4().hex[:8]}"
    staging_dir = snapshots_root / f".tmp-{final_dir.name}-{uuid.uuid4().hex}"
    moved_to_final = False

    try:
        staging_dir.mkdir(parents=True)
        pages_path = staging_dir / "pages.jsonl"
        with pages_path.open("w", encoding="utf-8") as file_obj:
            for page in pages:
                file_obj.write(json.dumps(page, ensure_ascii=False) + "\n")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at.astimezone(timezone.utc).isoformat(),
            "source_id": source_id,
            "mode": mode,
            "seed_url": seed_url or "",
            "counts": {"pages": len(pages)},
            "sha256": {"pages.jsonl": _sha256(pages_path)},
        }
        (staging_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        validate_snapshot(staging_dir)
        os.replace(staging_dir, final_dir)
        moved_to_final = True
        _replace_latest_symlink(profile_root, final_dir)
        return final_dir
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if moved_to_final and final_dir.exists():
            shutil.rmtree(final_dir)
        raise


def validate_snapshot(snapshot_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate a Confluence snapshot and return its manifest and pages."""

    manifest_path = snapshot_dir / "manifest.json"
    pages_path = snapshot_dir / "pages.jsonl"
    if not manifest_path.is_file() or not pages_path.is_file():
        raise FileNotFoundError(
            f"Confluence snapshot requires manifest.json and pages.jsonl in {snapshot_dir}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = [
        json.loads(line)
        for line in pages_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Confluence snapshot schema version")
    if manifest.get("counts") != {"pages": len(pages)}:
        raise ValueError("Confluence snapshot page count does not match manifest")
    if (manifest.get("sha256") or {}).get("pages.jsonl") != _sha256(pages_path):
        raise ValueError("Confluence snapshot checksum mismatch: pages.jsonl")

    source_id = str(manifest.get("source_id") or "")
    page_ids: set[str] = set()
    source_urls: set[str] = set()
    for page in pages:
        metadata = page.get("metadata") or {}
        page_id = str(metadata.get("confluence_page_id") or "")
        source_url = str(metadata.get("source_url") or "")
        if not page.get("page_content") or not page_id or not source_url:
            raise ValueError("Confluence snapshot contains an incomplete page")
        if metadata.get("source_id") != source_id:
            raise ValueError("Confluence page source_id does not match manifest")
        if page_id in page_ids or source_url in source_urls:
            raise ValueError(f"Duplicate Confluence page in snapshot: {page_id}")
        page_ids.add(page_id)
        source_urls.add(source_url)
    return manifest, pages


def _fetch_rest_page(
    session: requests.Session,
    *,
    page_url: str,
    source_id: str,
    expected_space: str,
    crawl_depth: int,
) -> dict[str, Any]:
    parsed = urlparse(page_url)
    context = "/confluence"
    base_url = f"{parsed.scheme}://{parsed.netloc}{context}"
    query = parse_qs(parsed.query)
    page_ids = query.get("pageId")
    params: dict[str, str] = {
        "expand": "body.view,version,history,space",
    }
    if page_ids:
        api_url = f"{base_url}/rest/api/content/{page_ids[0]}"
    else:
        marker = f"{context}/display/{expected_space}/"
        if marker not in parsed.path:
            raise ValueError(f"Unsupported Confluence page URL: {page_url}")
        title = unquote_plus(parsed.path.split(marker, 1)[1])
        api_url = f"{base_url}/rest/api/content"
        params.update({"spaceKey": expected_space, "title": title})

    response = session.get(api_url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and "results" in payload:
        results = payload.get("results") or []
        if len(results) != 1:
            raise ValueError(f"Expected one Confluence page for {page_url}, got {len(results)}")
        payload = results[0]
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid Confluence response for {page_url}")

    page_id = str(payload.get("id") or "")
    title = str(payload.get("title") or "")
    space = payload.get("space") or {}
    actual_space = str(space.get("key") or expected_space)
    if actual_space != expected_space:
        raise ValueError(f"Confluence page {page_id} is outside space {expected_space}")
    body = ((payload.get("body") or {}).get("view") or {}).get("value") or ""
    markdown = html_fragment_to_markdown(str(body), base_url=base_url)
    if not page_id or not title:
        raise ValueError(f"Confluence page is incomplete: {page_url}")
    if not markdown.strip():
        markdown = f"# {title}\n"
    version = payload.get("version") or {}
    history = payload.get("history") or {}
    updated_at = str(
        version.get("when")
        or (history.get("lastUpdated") or {}).get("when")
        or ""
    )
    canonical_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
    return _page_record(
        page_content=markdown,
        source_id=source_id,
        source_url=canonical_url,
        page_id=page_id,
        title=title,
        space_key=actual_space,
        version=str(version.get("number") or ""),
        updated_at=updated_at,
        crawl_depth=crawl_depth,
    )


def _page_record(
    *,
    page_content: str,
    source_id: str,
    source_url: str,
    page_id: str,
    title: str,
    space_key: str,
    version: str,
    updated_at: str,
    crawl_depth: int,
) -> dict[str, Any]:
    return {
        "page_content": page_content,
        "metadata": {
            "source": source_url,
            "source_path": source_url,
            "source_type": "confluence-snapshot",
            "source_format": "markdown",
            "source_id": source_id,
            "source_url": source_url,
            "confluence_page_id": page_id,
            "space_key": space_key,
            "title": title,
            "version": version,
            "updated_at": updated_at,
            "crawl_depth": crawl_depth,
        },
    }


def _render_node(node: Any, *, base_url: str) -> str:
    if isinstance(node, NavigableString):
        return re.sub(r"\s+", " ", str(node))
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if name == "br":
        return "\n"
    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(name[1])
        return f"\n\n{'#' * level} {_plain_text(node)}\n\n"
    if name == "pre":
        language = ""
        code = node.find("code")
        if code is not None:
            classes = code.get("class") or []
            language = next(
                (value.split("language-", 1)[1] for value in classes if value.startswith("language-")),
                "",
            )
        return f"\n\n```{language}\n{node.get_text().strip()}\n```\n\n"
    if name == "code":
        return f"`{node.get_text().strip()}`"
    if name == "a":
        label = _render_children(node, base_url=base_url).strip() or str(node.get("title") or "link")
        href = str(node.get("href") or "").strip()
        return f"[{label}]({urljoin(base_url, href)})" if href else label
    if name == "img":
        alt = str(node.get("alt") or node.get("title") or "image").strip()
        src = urljoin(base_url, str(node.get("src") or ""))
        return f"Image: {alt} ({src})" if src else f"Image: {alt}"
    if name == "table":
        return _render_table(node)
    if name in {"ul", "ol"}:
        ordered = name == "ol"
        items = []
        for index, item in enumerate(node.find_all("li", recursive=False), start=1):
            text = _render_children(item, base_url=base_url).strip()
            text = re.sub(r"\n+", " ", text)
            items.append(f"{index}. {text}" if ordered else f"- {text}")
        return "\n" + "\n".join(items) + "\n"
    children = _render_children(node, base_url=base_url)
    if name in {"p", "div", "section", "article", "blockquote"}:
        if name == "blockquote":
            children = "\n".join(f"> {line}" for line in children.strip().splitlines())
        return f"\n\n{children.strip()}\n\n" if children.strip() else ""
    if name in {"strong", "b"}:
        return f"**{children.strip()}**"
    if name in {"em", "i"}:
        return f"*{children.strip()}*"
    return children


def _render_children(node: Tag, *, base_url: str) -> str:
    return "".join(_render_node(child, base_url=base_url) for child in node.children)


def _render_table(table: Tag) -> str:
    rows: list[list[str]] = []
    header_present = False
    for row_index, row in enumerate(table.find_all("tr")):
        cells = row.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        if row_index == 0 and any(cell.name == "th" for cell in cells):
            header_present = True
        rows.append([_plain_text(cell).replace("|", "\\|") for cell in cells])
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    if header_present:
        header, body = rows[0], rows[1:]
    else:
        header = [f"Column {index}" for index in range(1, width + 1)]
        body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n\n" + "\n".join(lines) + "\n\n"


def _plain_text(node: Tag) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def _meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", id=name)
    return str(tag.get("content") or "").strip() if tag is not None else ""


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


def _has_substantive_content(text: str) -> bool:
    return len(re.sub(r"\s+", "", text)) >= 30


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for block in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _replace_latest_symlink(profile_root: Path, final_dir: Path) -> None:
    latest_path = profile_root / "latest"
    temporary_link = profile_root / f".latest-{uuid.uuid4().hex}"
    relative_target = Path("snapshots") / final_dir.name
    os.symlink(relative_target, temporary_link)
    try:
        os.replace(temporary_link, latest_path)
    finally:
        if temporary_link.is_symlink():
            temporary_link.unlink()
