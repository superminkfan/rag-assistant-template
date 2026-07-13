# RAG Assistant Template

Local CLI-first RAG assistant for Ignite/DataGrid documentation and incident analysis.

The project uses:

- local Ollama models for generation and embeddings;
- Chroma as a persistent vector store;
- metadata-first chunks for source-aware answers;
- a CLI interface for indexing, source inspection, question answering, and incident analysis.

## Architecture

The application layer depends on small protocols instead of concrete infrastructure libraries:

- `LLM` and `Retriever` are used by question answering and incident analysis;
- `Embeddings` and `VectorStore` are used by local indexing and retrieval;
- `adapters/` contains the Ollama, Chroma, and hybrid retrieval implementations;
- `factory.py` is the composition root for the default local stack.

This keeps Ollama and Chroma as the default runtime without coupling RAG scenarios to them. Tests
can use in-memory fake implementations and alternative providers can be added without changing
prompting or incident-analysis logic.

## Requirements

- Python 3.10 or higher.
- Ollama running locally.
- Ollama models:

```bash
ollama pull llama3.2:latest
ollama pull mxbai-embed-large
```

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For editable CLI script installation:

```bash
pip install -e .
```

## CLI

Create a local config file from the committed template:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your documentation paths, Jira endpoint, certificate path, and artifact
directory. The local `config.yaml` file is ignored by Git. Generated Chroma and Jira snapshot
artifacts default to `~/.rag-assistant/artifacts`, outside the repository.

Run the CLI with:

```bash
rag-assistant --config config.yaml --help
```

### Ingest datagrid-docs

Set `paths.datagrid_docs` in `config.yaml`, then build a local Chroma database:

```bash
rag-assistant --config config.yaml ingest \
  --source-type datagrid-docs \
  --reset
```

For a quick smoke test on a small subset:

```bash
rag-assistant --config config.yaml ingest \
  --source-type datagrid-docs \
  --limit 10 \
  --batch-size 16
```

### Ingest Ignite AsciiDoc docs

The repository also contains an Ignite AsciiDoc corpus in `data/`. Build an index from it with:

```bash
rag-assistant --config config.yaml ingest \
  --source-type ignite-docs \
  --reset
```

For a quick smoke test:

```bash
rag-assistant --config config.yaml ingest \
  --source-type ignite-docs \
  --limit 10 \
  --batch-size 16 \
  --reset
```

### Build a combined index

To mix DataGrid product documentation, Apache Ignite docs, and exported incident tickets in the
same Chroma database, reset once on the first source and append the others without `--reset`:

```bash
rag-assistant --config config.yaml ingest \
  --source-type datagrid-docs \
  --reset

rag-assistant --config config.yaml ingest \
  --source-type ignite-docs

rag-assistant --config config.yaml ingest \
  --source-type jira-snapshot
```

### Ingest the bundled ignite-firefighter knowledge base

The selected troubleshooting tree, GC notes, Stack Overflow/GitHub Q&A, and Apache Ignite user-list
archive are copied into `data/ignite-firefighter`. Their upstream commit and checksums are recorded
in `data/ignite-firefighter/manifest.json`.

Four independent source types are available:

- `ignite-firefighter-tree`
- `ignite-firefighter-notes`
- `stackoverflow-kb`
- `ignite-user-mailing-list`

Inspect and ingest them independently so each corpus can be refreshed or rolled back with
`--replace-source-type`. The exact validated commands, dry-run counts, backup location, trust
hierarchy, and retrieval behavior are documented in
[`docs/ignite-firefighter-kb.md`](docs/ignite-firefighter-kb.md).

### Snapshot and ingest Confluence pages

Confluence sources use an atomic local snapshot before embedding. Public Apache pages are fetched
through the Confluence REST API. The Design Documents profile includes the seed and its 38 direct
same-space links, without recursively crawling the rest of the wiki:

```bash
rag-assistant --config config.yaml snapshot-confluence \
  --source-id apache-ignite-design

rag-assistant --config config.yaml inspect-source \
  --source-type confluence-snapshot \
  --source-id apache-ignite-design

rag-assistant --config config.yaml ingest \
  --source-type confluence-snapshot \
  --source-id apache-ignite-design \
  --replace-source-id
```

Private SberWorks pages are imported from browser-saved HTML without a network request. The
`sberworks` profile finds and validates the five configured page ids in the supplied directory;
unrelated HTML files are ignored:

```bash
rag-assistant --config config.yaml snapshot-confluence \
  --source-id sberworks \
  --offline-dir ~/Downloads

rag-assistant --config config.yaml inspect-source \
  --source-type confluence-snapshot \
  --source-id sberworks

rag-assistant --config config.yaml ingest \
  --source-type confluence-snapshot \
  --source-id sberworks \
  --replace-source-id
```

Snapshots are published under `confluence.output_root/<source-id>/snapshots/`; `latest` changes only
after page counts, unique ids, required metadata, and checksums have been validated. Text, headings,
lists, tables, code blocks, panels, links, and image alt text are retained. Attachments and OCR are
not included.

### Export and ingest Jira snapshots

Jira credentials are read from environment variables:

- `UNAME`
- `PASSWD`

Set `jira.base_url`, `jira.jql`, and `jira.cert_path` in `config.yaml`. Export all issues whose
summary starts with `[SBTSUPPORT-<number>]`:

```bash
export UNAME="your-username"
export PASSWD="your-password"
python scripts/jira/export_support_tickets.py --config config.yaml
```

For a small smoke test that writes a valid snapshot with only a few matching tickets:

```bash
python scripts/jira/export_support_tickets.py --config config.yaml --limit 3
```

The exporter writes an atomic snapshot under `jira.output_root` and updates the `latest` symlink only
after validation. Each snapshot contains:

```text
full/issues.csv
full/comments.csv
curated/issues.csv
curated/comments.csv
manifest.json
```

The full variant preserves every matching ticket. The curated variant requires a non-empty client
description and at least one comment with 30 non-whitespace characters. Cancelled, executor-rejected,
duplicate, rejected, and incomplete tickets are excluded. Missing Jira resolution is retained and
recorded as a quality flag.

Descriptions and comments remain raw source material. The exporter only masks explicit private keys,
authorization values, JWTs, passwords, tokens, and similarly named secrets. Attachments are not
downloaded; their ids, names, MIME types, and sizes are stored in issue metadata.

Build the canonical incident index from the curated snapshot:

```bash
rag-assistant --config config.yaml ingest \
  --source-type jira-snapshot \
  --replace-source-type
```

The snapshot loader creates one source document for the client request and one for each Jira comment.
Every comment chunk repeats the issue key, support key, title, comment id, author, and date. This keeps
long technical discussions attributable after chunking.

### Ask a question

```bash
rag-assistant --config config.yaml ask "Как проверить проблемы с WAL и checkpointing?"
```

While the request is running in an interactive terminal, the CLI shows an animated activity
indicator. After the answer it prints the total response time. Redirected output does not include
the animation.

When using zsh, quote questions that contain `?` or wildcard characters.

### Analyze an incident

Prepare a text file with symptoms, logs, metrics, versions, and timeline, then run:

```bash
rag-assistant --config config.yaml analyze-incident ./incident.txt
```

The output is structured as:

- `Summary`
- `Likely Cause`
- `Evidence`
- `Diagnostics`
- `Mitigation`
- `Risk / Caveats`
- `Confidence`
- `Sources`

### Inspect the index

Check what is stored in Chroma without calling Ollama:

```bash
rag-assistant --config config.yaml inspect-index
```

For large indexes, inspect a metadata sample:

```bash
rag-assistant --config config.yaml inspect-index --sample-limit 1000
```

### Inspect a source before embedding

Dry-run a loader and chunker without calling Ollama or writing Chroma:

```bash
rag-assistant --config config.yaml inspect-source --source-type ignite-docs
rag-assistant --config config.yaml inspect-source \
  --source-type jira-snapshot
rag-assistant --config config.yaml inspect-source \
  --source-type datagrid-docs
```

## Metadata-first chunks

Each chunk stores more than raw text. The datagrid-docs loader attaches:

- `source_type`
- `source_format`
- `source_path`
- `doc_set_code`
- `product`
- `product_version`
- `release_id`
- `archive_group_id`
- `guide`
- `component`
- `title`
- `issue_key` and `support_key` for Jira snapshot records
- `section`
- `chunk_index`
- `chunk_id`

Confluence chunks additionally include `source_id`, `source_url`, `confluence_page_id`, `space_key`,
`version`, `updated_at`, and `crawl_depth`. Use `--replace-source-id` when refreshing one Confluence
profile so other sources remain untouched.

The ignite-firefighter corpora add `record_id`, `record_type`, `source_url`, `source_commit`,
`trust_tier`, `authority_score`, `quality_score`, `product_version`, `published_at`, and
format-specific fields such as tags, answer score, accepted status, or mailing-list thread id.

This makes incident retrieval more useful than plain semantic search: answers can cite exact files,
sections, product versions, and coarse components such as `persistence`, `cluster`, `security`,
`performance`, `cdc`, or `monitoring`.

## Retrieval

The CLI uses hybrid retrieval:

- vector search through Chroma and Ollama embeddings;
- lightweight keyword search over the local Chroma collection;
- deterministic reranking and final context formatting with deterministic citations;
- strong-token filtering for incident-like queries, so exact terms such as `os::commit_memory`,
  `RMI`, `TCP`, `WAL`, `checkpoint`, or exception names are not drowned out by generic vector matches.

This helps with incident terms such as exception names, configuration keys, log phrases, WAL,
checkpointing, PME, topology changes, and other exact strings that pure vector search can miss.

### Retrieval parameters

The `retrieval` section controls how many chunks are considered before the assistant builds the
final prompt:

```yaml
retrieval:
  vector_k: 24
  keyword_k: 32
  final_k: 6
```

`vector_k` is the number of candidates returned by semantic search through Chroma and Ollama
embeddings. Increase it when answers miss conceptually related documentation. Higher values improve
recall but make retrieval slower.

`keyword_k` is the number of candidates returned by exact-token keyword search over the local
collection. Increase it for incident analysis with exception names, configuration keys, log phrases,
WAL, PME, checkpointing, topology versions, or other exact technical strings. Higher values make the
keyword pass consider more chunks before reranking.

`final_k` is the number of chunks kept after merging and reranking candidates. These chunks are
inserted into the LLM prompt and appear in `Sources`. Keep this much smaller than `vector_k` and
`keyword_k`; increasing it can help questions that need several independent sources, but it also
increases prompt size and the chance of noisy context.

The default profile, `vector_k: 24`, `keyword_k: 32`, `final_k: 6`, searches broadly first and then
keeps a compact final context.

## Smoke Testing

Small mixed index:

```bash
rag-assistant --config config.yaml ingest \
  --source-type datagrid-docs \
  --limit 8 \
  --batch-size 16 \
  --reset

rag-assistant --config config.yaml ingest \
  --source-type ignite-docs \
  --limit 8 \
  --batch-size 16

rag-assistant --config config.yaml ingest \
  --source-type jira-snapshot \
  --limit 3 \
  --batch-size 16

rag-assistant --config config.yaml inspect-index
rag-assistant --config config.yaml inspect-source \
  --source-type jira-snapshot
rag-assistant --config config.yaml analyze-incident ./incident.txt
```

## Project structure

```text
.
├── config.example.yaml
├── docs/
│   └── datagrid-docs-inventory.md
├── src/rag_assistant/
│   ├── cli.py
│   ├── config.py
│   ├── docs.py
│   ├── indexing.py
│   ├── rag.py
│   ├── retrieval.py
│   └── settings.py
├── scripts/
│   └── jira/
├── tests/
└── pyproject.toml
```

## Roadmap

- Add incremental deletion of stale chunks when documents are removed.
- Add a stronger reranker when local model/runtime constraints are clear.
- Add optional incremental Jira refreshes if full snapshots become too slow.
