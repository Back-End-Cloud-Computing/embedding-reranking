# embedding-reranking

Embedding generation and reranking microservice for the GANJJ e-commerce
platform, built with **FastAPI** + `sentence-transformers`. It owns the
*write* path into `vector-db` (indexing) — domain services never generate
embeddings or write to `vector-db` themselves. Reading is different: a domain
service embeds its own query text via `/embed`, searches `vector-db` directly,
then optionally reranks the candidates it got back via `/rerank` here. This
service never touches `vector-db` for reads, and has no collection/query
knowledge at all for reranking.

## Scope

- Generates text embeddings in batch, off the event loop (`asyncio.to_thread`),
  using a free/open-source multilingual model
  (`paraphrase-multilingual-MiniLM-L12-v2` by default), suitable for Portuguese.
- Indexes one entity's embedding into a caller-specified `vector-db` collection
  (`POST /index`), generic across entity types: the caller states its own
  `collection_name` and `id` (product-service uses `"products"` today; a
  future domain service would use its own collection name without any change
  here). Any existing vector under that same id is deleted first, so
  re-indexing (or a retried call) never leaves duplicate rows behind.
- Reranks a caller-supplied list of passages by relevance to a query
  (`POST /rerank`), via cosine similarity between their embeddings (the same
  bi-encoder model used for indexing - no separate cross-encoder to load).
  Pure function: no vector-db or collection knowledge, so it works on
  candidates from anywhere.
- Does **not** run searches or access ChromaDB for reads — domain services
  embed their own query text via `/embed` and call `vector-db`'s search
  directly, then rerank the results here if they want reordering.
- Does **not** contain business prompts or domain-specific text building —
  callers send ready-to-embed text and their own metadata.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/embed` | Batch-embed a list of texts. No side effects. |
| POST | `/index` | Embed one entity's text and (re)index it into a `vector-db` collection. |
| POST | `/rerank` | Reorder caller-supplied passages by relevance to a query. |
| GET | `/health` | Liveness check. |

## Stack

| Concern | Choice |
|---|---|
| API framework | FastAPI (async), Pydantic v2 |
| Embeddings | `sentence-transformers` — `paraphrase-multilingual-MiniLM-L12-v2` |
| Vector store client | `httpx` calls to the `vector-db` service (no direct ChromaDB access) |
| Tests | pytest, pytest-asyncio, respx (HTTP mocking) |
| Runtime | Docker + Docker Compose |

## Running tests

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

## Running locally

```bash
docker build -t embedding-reranking .
docker run -p 8003:8003 --env-file .env embedding-reranking
```

Interactive API docs (Swagger) are available at `/docs` once running.
