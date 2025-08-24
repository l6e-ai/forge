I'll draft a concrete implementation plan as a structured todo list for adding built-in memory (vector store + embeddings) with defaults, touching config, runtime, API, templates, CLI, compose, packaging, and tests.
Ran tool
Proposed tasks to add built-in memory (vector store + embeddings):

- CLI: memory upsert/search/import; embedding doctor
- Auto-models: suggest/select embedding model; persist to config
- Compose: infer optional qdrant/redis; document volumes/ports
- Packaging: persist memory config; zero extra deps for in-memory default
- Docs: README + doc page for memory/embeddings with examples
- Tests: unit (similarity, EmbeddingService), integration (save/query)
- Monitor UI: optional panel to view memory inserts/searches
- Security/limits: size caps, rate limits, and redaction knobs