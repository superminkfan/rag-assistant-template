import os
import requests
import urllib3
from typing import Dict, Any, List

# --- Settings ---
BASE_JIRA_URL = os.environ.get("JIRA_BASE", "https://sberworks.ru/jira")

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
    """Return a list of issue keys matching the JQL.
    Only issue keys are returned here to keep it minimal and fast.
    """
    url = f"{BASE_JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "startAt": start_at,
        "maxResults": max_results,
        # We don't need fields here; keys always come back.
        "fields": "none",
    }
    r = session.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return [it["key"] for it in data.get("issues", [])]


def get_issue_basic(session: requests.Session, issue_key: str) -> Dict[str, Any]:
    """Fetch just the basic fields we need from a single issue: summary & description.
    Returns dict: {"key", "summary", "description"}
    """
    url = f"{BASE_JIRA_URL}/rest/api/2/issue/{issue_key}"
    params = {
        "fields": "summary,description",
        # You can add 'expand': 'renderedFields' if you want rendered HTML for description
    }
    r = session.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    fields = data.get("fields", {})
    return {
        "key": data.get("key", issue_key),
        "summary": fields.get("summary"),
        "description": fields.get("description"),
    }


def get_issue_comments(session: requests.Session, issue_key: str, start_at: int = 0, max_results: int = 1000) -> List[Dict[str, Any]]:
    """Fetch all comments for an issue (paged). Returns a list of {author, created, body} dicts."""
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
            "author": author_name,
            "created": c.get("created"),
            "updated": c.get("updated"),
            "body": c.get("body"),
        })
    return comments

# --- Example usage (no saving/exporting, just access) ---
if __name__ == "__main__":
    JQL = os.environ.get("JQL", "project = ISE ORDER BY updated DESC")
    session = get_session()

    keys = search_issue_keys(session, JQL, max_results=20)
    print(f"Found {len(keys)} issues for JQL: {JQL}")

    for k in keys:
        basic = get_issue_basic(session, k)
        comments = get_issue_comments(session, k)
        print("\n---", k, "---")
        print("Summary:", basic["summary"])  # str or None
        print("Description:", (basic["description"] or "").strip()[:300], "...")
        print(f"Comments: {len(comments)}")
        # for i, c in enumerate(comments[:3]):
        #     print(f"  [{i+1}] {c['author']} @ {c['created']}:\n{(c['body'] or '').strip()[:300]}\n")
