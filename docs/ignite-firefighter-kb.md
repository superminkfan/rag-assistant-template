# ignite-firefighter knowledge-base integration

The repository contains a reproducible copy of the selected `ignite-firefighter` knowledge
corpora under `data/ignite-firefighter`. The bundle manifest records the upstream commit and
SHA-256 checksum of every ingest input.

## Backup

Before this integration was implemented, the existing Chroma database was copied and verified with
`diff -qr`:

- database: `/Users/zikunov_semen/PycharmProjects/Chroma`
- backup: `/Users/zikunov_semen/PycharmProjects/Chroma.backup-20260624-pre-ignite-firefighter`

No new embeddings were generated while implementing this integration.

## Source types

| Source type | Input | Normalized documents | Dry-run chunks |
| --- | --- | ---: | ---: |
| `ignite-firefighter-tree` | structured troubleshooting YAML | 331 | 434 |
| `ignite-firefighter-notes` | GC collector troubleshooting Markdown | 1 | 23 |
| `stackoverflow-kb` | Stack Overflow and GitHub question/response JSONL | 2,645 | 16,370 |
| `ignite-user-mailing-list` | gzip mbox from `user@ignite.apache.org` | 499 | 1,175 |

Counts use the default `chunk_size=1200` and `chunk_overlap=180`.

The tree loader creates separate provenance, fact, action, decision-node, and checklist records.
Decision nodes contain the resolved action details, not only an action id. Question/response and
mail records repeat their record identity, trust tier, version, date, tags, and source context in
every chunk.

## Retrieval policy

Each new record has scalar Chroma metadata for record identity, type, trust tier, authority,
quality, product version, publication date, and source URL. Retrieval applies this order:

1. official DataGrid/Ignite and authoritative Confluence documentation;
2. curated troubleshooting tree and GC notes;
3. internal Jira case history;
4. Stack Overflow and GitHub community records;
5. the experimental mailing-list corpus.

Explicit product-version matches are boosted. Final context is limited to two chunks from one
record and is diversified across source types. Community freshness, accepted-answer state, and
quality score are secondary ranking signals.

The Chroma adapter maintains `rag_lexical.sqlite3`, a persistent SQLite FTS5/BM25 sidecar. During
the first write or keyword search it verifies the document count and rebuilds the sidecar if it is
missing or stale. Subsequent lexical retrieval does not scan every Chroma document.

## Validation

Before embedding, run the source inspection commands below. They validate bundle checksums,
manifests, structured references, stable chunk ids, metadata distributions, and expected counts.

```bash
rag-assistant --config config.yaml inspect-source --source-type ignite-firefighter-tree
rag-assistant --config config.yaml inspect-source --source-type ignite-firefighter-notes
rag-assistant --config config.yaml inspect-source --source-type stackoverflow-kb
rag-assistant --config config.yaml inspect-source --source-type ignite-user-mailing-list
```

## Ingest commands

Run these only when the local Ollama embedding runtime is available. Do not use `--reset`: the
existing DataGrid, Ignite, Jira, and Confluence chunks must remain in the combined index.

```bash
rag-assistant --config config.yaml ingest \
  --source-type ignite-firefighter-tree \
  --replace-source-type

rag-assistant --config config.yaml ingest \
  --source-type ignite-firefighter-notes \
  --replace-source-type

rag-assistant --config config.yaml ingest \
  --source-type stackoverflow-kb \
  --replace-source-type

rag-assistant --config config.yaml ingest \
  --source-type ignite-user-mailing-list \
  --replace-source-type
```

After all four commands complete, verify the combined index:

```bash
rag-assistant --config config.yaml inspect-index
```

Then run the 40-case retrieval benchmark. It performs retrieval and embedding queries but does not
call the generation model:

```bash
rag-assistant --config config.yaml evaluate-retrieval
```

The report includes expected-term recall, component recall, preferred-source recall, citation
readiness, and failed cases. Keep its output as the post-ingest baseline for future corpus refreshes.
