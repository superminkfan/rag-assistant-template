"""Count Jira issues whose summaries start with an SBTSUPPORT tag."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import requests
import urllib3

from rag_assistant.config import load_config


JIRA_USERNAME_ENV = "UNAME"
JIRA_PASSWORD_ENV = "PASSWD"
SUPPORT_TAG_RE = re.compile(r"^\[SBTSUPPORT")
PAGE_SIZE = 100

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_session(*, cert_path: Path) -> requests.Session:
    """Create an authenticated Jira session without exposing credentials."""

    if not cert_path.is_file():
        raise FileNotFoundError(f"Client certificate not found: {cert_path}")
    username = os.getenv(JIRA_USERNAME_ENV)
    password = os.getenv(JIRA_PASSWORD_ENV)
    if not username or not password:
        raise RuntimeError(
            f"Set {JIRA_USERNAME_ENV} and {JIRA_PASSWORD_ENV} before reading Jira."
        )

    session = requests.Session()
    session.auth = (username, password)
    session.cert = str(cert_path)
    session.verify = False
    return session


def fetch_issue_page(
    session: requests.Session,
    *,
    base_url: str,
    jql: str,
    start_at: int,
) -> dict[str, Any]:
    """Fetch one page of issue keys and summaries."""

    response = session.get(
        f"{base_url}/rest/api/2/search",
        params={
            "jql": jql,
            "startAt": start_at,
            "maxResults": PAGE_SIZE,
            "fields": "summary",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def count_support_tickets(
    session: requests.Session,
    *,
    base_url: str,
    jql: str,
) -> tuple[int, int]:
    """Return the number of matching tickets and all scanned tickets."""

    matching = 0
    scanned = 0
    start_at = 0

    while True:
        page = fetch_issue_page(
            session,
            base_url=base_url,
            jql=jql,
            start_at=start_at,
        )
        issues = page.get("issues") or []

        for issue in issues:
            fields = issue.get("fields") or {}
            summary = fields.get("summary") or ""
            scanned += 1
            if SUPPORT_TAG_RE.match(summary):
                matching += 1

        total = int(page.get("total") or 0)
        if not issues or start_at + len(issues) >= total:
            return matching, scanned

        start_at += len(issues)
        print(f"Scanned {scanned}/{total} tickets...", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count Jira issues whose summaries start with an SBTSUPPORT tag."
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--jira-base", default=None)
    parser.add_argument("--jql", default=None)
    parser.add_argument("--cert-path", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    base_url = args.jira_base or config.jira.base_url
    jql = args.jql or config.jira.jql
    cert_path = args.cert_path or config.jira.cert_path
    if not base_url:
        raise RuntimeError("Set jira.base_url in config or pass --jira-base.")
    if not jql:
        raise RuntimeError("Set jira.jql in config or pass --jql.")
    if cert_path is None:
        raise RuntimeError("Set jira.cert_path in config or pass --cert-path.")

    session = build_session(cert_path=cert_path)
    matching, scanned = count_support_tickets(
        session,
        base_url=base_url.rstrip("/"),
        jql=jql,
    )
    print(f"Scanned tickets: {scanned}")
    print(f"Tickets starting with [SBTSUPPORT-<number>]: {matching}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
