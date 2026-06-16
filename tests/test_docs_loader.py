from rag_assistant.docs import (
    extract_first_heading,
    extract_first_asciidoc_heading,
    infer_component,
    iter_asciidoc_sections,
    iter_markdown_sections,
    load_asciidoc_source,
    load_markdown_source,
    normalize_markdown,
    normalize_asciidoc,
    read_doc_manifest,
)


def test_read_doc_manifest_parses_product_metadata(tmp_path):
    doc_yaml = tmp_path / "doc.yaml"
    doc_yaml.write_text(
        """code: IGN
version: 18.0.0
sberproject_release_id: IGN.34

substitutions:
  prod_version: 18.0.0
""",
        encoding="utf-8",
    )

    manifest = read_doc_manifest(doc_yaml)

    assert manifest["code"] == "IGN"
    assert manifest["version"] == "18.0.0"
    assert manifest["sberproject_release_id"] == "IGN.34"
    assert manifest["substitutions"]["prod_version"] == "18.0.0"


def test_normalize_markdown_preserves_directive_context():
    raw = """# Title

::::{md-tab-set}
:::{md-tab-item} XML
:::{code-block} xml
:caption: Example
<bean />
:::
::::

:::{admonition} Внимание
:class: danger
Use {{prod_version}}.
:::
"""

    normalized = normalize_markdown(raw, substitutions={"prod_version": "18.0.0"})

    assert "Tab: XML" in normalized
    assert "Code block: xml" in normalized
    assert "Admonition: Внимание" in normalized
    assert "Use 18.0.0." in normalized
    assert ":caption:" not in normalized


def test_load_markdown_source_adds_metadata(tmp_path):
    docs_root = tmp_path / "documentation" / "documents" / "troubleshooting-and-performance"
    docs_root.mkdir(parents=True)
    (tmp_path / "documentation" / "doc.yaml").write_text(
        """code: IGN
version: 18.0.0
sberproject_release_id: IGN.34
archive_group_id: group
""",
        encoding="utf-8",
    )
    (docs_root / "performance-tuning.md").write_text(
        "# Настройка производительности\n\n## WAL\n\nText",
        encoding="utf-8",
    )

    documents = load_markdown_source(tmp_path)

    assert len(documents) == 1
    metadata = documents[0].metadata
    assert metadata["source_type"] == "datagrid-docs"
    assert metadata["doc_set_code"] == "IGN"
    assert metadata["product_version"] == "18.0.0"
    assert metadata["guide"] == "troubleshooting-and-performance"
    assert metadata["component"] == "performance"
    assert metadata["title"] == "Настройка производительности"


def test_normalize_asciidoc_collapses_tabs_and_metadata():
    raw = """= Title
:toc:

[tabs]
====
tab:Unix[]
--
echo ok
--
tab:Windows[]
--
dir
--
====

include::includes/example.adoc[]
image::images/a.png[Diagram]
"""

    normalized = normalize_asciidoc(raw)

    assert ":toc:" not in normalized
    assert "echo ok" in normalized
    assert "dir" not in normalized
    assert "Include: includes/example.adoc" in normalized
    assert "Image: images/a.png (Diagram)" in normalized


def test_load_asciidoc_source_adds_ignite_metadata(tmp_path):
    guide_dir = tmp_path / "persistence"
    guide_dir.mkdir()
    (guide_dir / "native-persistence.adoc").write_text(
        "= Native Persistence\n\n== WAL\n\nContent",
        encoding="utf-8",
    )

    documents = load_asciidoc_source(tmp_path)

    assert len(documents) == 1
    metadata = documents[0].metadata
    assert metadata["source_type"] == "ignite-docs"
    assert metadata["source_format"] == "asciidoc"
    assert metadata["product"] == "Ignite"
    assert metadata["guide"] == "persistence"
    assert metadata["component"] == "persistence"
    assert metadata["title"] == "Native Persistence"


def test_iter_markdown_sections_tracks_heading_path():
    document = load_source_doc(
        "# Root\n\nIntro\n\n## Child\n\nDetails\n\n### Leaf\n\nMore\n"
    )

    sections = list(iter_markdown_sections(document))

    assert [section.metadata["section"] for section in sections] == [
        "Root",
        "Root > Child",
        "Root > Child > Leaf",
    ]


def test_iter_asciidoc_sections_tracks_heading_path():
    document = load_source_doc(
        "= Root\n\nIntro\n\n== Child\n\nDetails\n\n=== Leaf\n\nMore\n",
        source_format="asciidoc",
    )

    sections = list(iter_asciidoc_sections(document))

    assert [section.metadata["section"] for section in sections] == [
        "Root",
        "Root > Child",
        "Root > Child > Leaf",
    ]


def test_extract_first_heading_and_component_inference():
    assert extract_first_heading("text\n# Heading\n") == "Heading"
    assert extract_first_asciidoc_heading("text\n= Heading\n") == "Heading"
    assert infer_component("developer-guide-IGNT", "datagrid_persistence", "Title") == "persistence"
    assert infer_component("security-guide", "index", "Security") == "security"


def load_source_doc(text, *, source_format="markdown"):
    from rag_assistant.docs import SourceDocument

    return SourceDocument(
        page_content=text,
        metadata={
            "source": "doc.md",
            "source_path": "doc.md",
            "source_format": source_format,
            "title": "Root",
        },
    )
