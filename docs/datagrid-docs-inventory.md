# datagrid-docs inventory

Source repository:

- GitHub: `superminkfan/datagrid-docs`
- Local path: `/Users/zikunov_semen/IdeaProjects/datagrid-docs`
- Branch observed locally: `main`

## Repository shape

The repository is documentation-first. The root has only a small utility layer and the actual content
is under `documentation/`.

Important paths:

- `documentation/doc.yaml` - product-level metadata.
- `documentation/documents/**` - Markdown documentation pages.
- `documentation/documents/**/resources/**` - images, XML snippets, JSON files, diagrams.
- `utils/fast_gen.py` - helper that generates JVM option tables from JSON.

## doc.yaml metadata

Observed values:

- `code`: `IGN`
- `version`: `18.0.0`
- `sberproject_release_id`: `IGN.34`
- `archive_group_id`: `sbt_PROD.CI90000012_ise`
- `substitutions.prod_version`: `18.0.0`

These values should become default metadata on all chunks produced from this repository.

## Content profile

Observed file types:

- Markdown: 289 files.
- PNG/JPG/JPEG/SVG images: 245 files.
- XML: 9 files.
- JSON: 4 files.
- Draw.io diagrams: 2 files.
- YAML: 1 file.

Main documentation sections:

- `about`
- `administration-guide`
- `architecture`
- `bank-instructions`
- `deployment-diagrams`
- `developer-guide-IGNT`
- `installation-guide`
- `pmi`
- `release-notes`
- `rest-api`
- `security-guide`
- `troubleshooting-and-performance`

The most incident-relevant sections are:

- `administration-guide`, especially `primary-analysis-of-logs.md`, `log-analyzer.md`, `monitoring.md`, `operational-commands.md`, `performance-statistics.md`.
- `troubleshooting-and-performance`, especially `performance-tuning.md`, `faq.md`, `sysctl-parameters.md`.
- `developer-guide-IGNT`, especially persistence, WAL, data regions, rebalancing, partition loss, baseline topology, networking.
- `release-notes` for version-aware behavior changes and fixed bugs.

## Markdown dialect

The documents are Markdown with MyST/Sphinx-style directives:

- `:::{admonition} ...`
- `::::{md-tab-set}`
- `::::{md-tab-item} XML`
- `:::{code-block} xml`
- `::::{list-table}`

The ingestion pipeline should not drop these blocks blindly. For RAG, tab labels and admonition
titles are useful context, so the loader should normalize them into plain text headings/labels before
chunking.

## Ingestion implications

The old AsciiDoc loader is not enough for this repository. The new loader should:

- Read `doc.yaml` once and attach product metadata to every chunk.
- Walk `documentation/documents/**/*.md`.
- Extract first-level title and heading path from Markdown headings.
- Infer `guide` and rough `component` from the path.
- Apply substitutions such as `{{prod_version}}`.
- Normalize MyST directives into readable text.
- Create stable chunk ids from source path and chunk index.
- Store rich metadata with every chunk: source type, product code, product version, release id, guide,
  title, section path, source path, and chunk index.

This structure is a better fit for incident analysis than the current plain `source` metadata.
