import os
import re
import csv
import requests
import urllib3
from typing import Dict, Any, List

# --- Settings ---
BASE_JIRA_URL = os.environ.get("JIRA_BASE", "https://sberworks.ru/jira")
DEFAULT_JQL = os.environ.get("JQL", "project = ISE ORDER BY updated DESC")
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "100"))
OUTPUT_CSV = os.environ.get("OUTPUT_CSV", "export/jira_issues.csv")

# Отбираем только задачи, у которых название начинается с тега смежного пространства вида
#   [SBTSUPPORT-62174] ...
SUPPORT_TAG_RE = re.compile(r"^\[SBTSUPPORT-\d+\]")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Authenticated session (login+password+client certificate) ---
def get_session() -> requests.Session:
    s = requests.Session()
    s.auth = (os.environ["UNAME"], os.environ["PASSWD"])  # username/password
    s.verify = False                                        # allow self-signed/internal CA
    s.cert = os.environ["CERT_PATH"]                       # path to client cert (PEM or (cert,key))
    return s

# --- Core Jira helpers (minimal) ---

def search_issue_keys(session: requests.Session, jql: str, start_at: int = 0, max_results: int = 50) -> List[str]:
    """Return a list of issue keys matching the JQL (paged)."""
    url = f"{BASE_JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "startAt": start_at,
        "maxResults": max_results,
        "fields": "none",
    }
    r = session.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return [it["key"] for it in data.get("issues", [])]


def get_issue_basic(session: requests.Session, issue_key: str) -> Dict[str, Any]:
    """Fetch just the fields we need: summary & description."""
    url = f"{BASE_JIRA_URL}/rest/api/2/issue/{issue_key}"
    params = {"fields": "summary,description"}
    r = session.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    fields = data.get("fields", {})
    return {
        "key": data.get("key", issue_key),
        "summary": fields.get("summary") or "",
        "description": fields.get("description") or "",
    }


def get_issue_comments(session: requests.Session, issue_key: str, start_at: int = 0, max_results: int = 1000) -> List[Dict[str, Any]]:
    """Fetch comments for an issue. Returns a list of {author, created, updated, body}."""
    url = f"{BASE_JIRA_URL}/rest/api/2/issue/{issue_key}/comment"
    params = {"startAt": start_at, "maxResults": max_results}
    r = session.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    comments: List[Dict[str, Any]] = []
    for c in data.get("comments", []):
        author_name = None
        author = c.get("author") or {}
        if isinstance(author, dict):
            author_name = author.get("displayName") or author.get("name")
        comments.append({
            "author": author_name or "",
            "created": c.get("created") or "",
            "updated": c.get("updated") or "",
            "body": c.get("body") or "",
        })
    return comments

# --- Filter & export ---

def title_has_support_tag(title: str) -> bool:
    return bool(SUPPORT_TAG_RE.match(title or ""))


def collect_filtered_issues(session: requests.Session, jql: str, limit: int = MAX_RESULTS) -> List[Dict[str, Any]]:
    """Search issues by JQL, fetch details, filter by title regex, return rows for export."""
    gathered: List[Dict[str, Any]] = []
    start = 0
    page_size = 100

    while len(gathered) < limit:
        keys = search_issue_keys(session, jql, start_at=start, max_results=page_size)
        if not keys:
            break
        for k in keys:
            basic = get_issue_basic(session, k)
            if not title_has_support_tag(basic["summary"]):
                continue
            comments = get_issue_comments(session, k)
            # Сшиваем комментарии в один текст для табличного поля
            comments_joined = "".join(f"{i+1}. {c['author']} @ {c['created']}{c['body']}" for i, c in enumerate(comments))
            gathered.append({
                "Идентификатор ISE": basic["key"],
                "Название": basic["summary"],
                "Описание": basic["description"],
                "Комментарии": comments_joined,
            })
            if len(gathered) >= limit:
                break
        start += page_size
    return gathered


def save_rows_to_csv(rows: List[Dict[str, Any]], path: str = OUTPUT_CSV) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["Идентификатор ISE", "Название", "Описание", "Комментарии"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path

# --- Example CLI ---
if __name__ == "__main__":
    session = get_session()
    rows = collect_filtered_issues(session, DEFAULT_JQL, limit=MAX_RESULTS)
    print(f"Отфильтровано задач: {len(rows)} (по шаблону названия [SBTSUPPORT-<num>])")
    out = save_rows_to_csv(rows, OUTPUT_CSV)
    print(f"Сохранено в: {out}")
