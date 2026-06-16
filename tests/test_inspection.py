from rag_assistant.inspection import format_index_summary, format_source_summary, inspect_source


def test_format_index_summary_lists_metadata_counts():
    summary = {
        "db_path": "/tmp/db",
        "collections": [
            {
                "name": "langchain",
                "count": 12,
                "sampled": 12,
                "source_type": {"ignite-docs": 7, "datagrid-docs": 5},
                "component": {"persistence": 4},
                "guide": {"SQL": 3},
            }
        ],
    }

    text = format_index_summary(summary)

    assert "Index: /tmp/db" in text
    assert "Collection: langchain" in text
    assert "Chunks: 12" in text
    assert "Source types: ignite-docs=7, datagrid-docs=5" in text
    assert "Components: persistence=4" in text


def test_inspect_source_dry_runs_loader_and_chunker(tmp_path):
    docs_dir = tmp_path / "persistence"
    docs_dir.mkdir()
    (docs_dir / "native-persistence.adoc").write_text(
        "= Native Persistence\n\n== WAL\n\nContent",
        encoding="utf-8",
    )

    summary = inspect_source(tmp_path, source_type="ignite-docs")
    text = format_source_summary(summary)

    assert summary["documents"] == 1
    assert summary["chunks"] >= 1
    assert summary["unique_chunk_ids"] == summary["chunks"]
    assert "Source type: ignite-docs" in text
    assert "Components: persistence=" in text
