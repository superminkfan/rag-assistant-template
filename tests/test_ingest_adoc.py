from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_load_documents_only_adoc(tmp_path):
    from scripts.ingest_adoc import load_documents

    adoc_file = tmp_path / "sample.adoc"
    adoc_file.write_text("= Title\n\nContent", encoding="utf-8")

    md_file = tmp_path / "ignore.md"
    md_file.write_text("# Heading", encoding="utf-8")

    documents = load_documents(Path(tmp_path), file_extensions=(".adoc",))

    assert len(documents) == 1
    assert documents[0].metadata.get("source", "").endswith("sample.adoc")


def test_preprocess_tabs_content_unix_only():
    from scripts.ingest_adoc import preprocess_tabs_content

    raw_content = """Intro text
[tabs]
====
tab:Unix[]
--
[source,bash]
----
echo 'hello'
----
--
tab:Unix[]
--
[source,bash]
----
echo 'hello'
----
--
tab:Windows[]
--
dir
--
====
Outro text
"""

    expected = """Intro text
[source,bash]
----
echo 'hello'
----
Outro text
"""

    assert preprocess_tabs_content(raw_content) == expected
