# Confluence snapshots

This directory contains validated, normalized snapshots used for repeatable ingest.

```bash
rag-assistant --config config.yaml ingest \
  --source data/confluence/sberworks \
  --source-type confluence-snapshot \
  --replace-source-id

rag-assistant --config config.yaml ingest \
  --source data/confluence/apache-ignite-design \
  --source-type confluence-snapshot \
  --replace-source-id
```

Each source directory contains `manifest.json` and `pages.jsonl`. The loader validates the page
count, source id, unique page ids and URLs, and the `pages.jsonl` checksum before chunking.
