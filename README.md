# embedding-reranking

Embedding generation microservice for the GANJJ e-commerce platform, built with
**FastAPI** + `sentence-transformers`. It is the only service allowed to call
`vector-db` for indexing or searching vectors — domain services (`product-service`
today, others later) never talk to `vector-db` directly for those operations.

## Scope

- Generates text embeddings in batch, off the event loop (`asyncio.to_thread`),
  using a free/open-source multilingual model
  (`paraphrase-multilingual-MiniLM-L12-v2` by default), suitable for Portuguese.
- Indexes one entity's embedding into a caller-specified `vector-db` collection
  (`POST /index`). Generic across entity types: the caller states its own
  `collection_name` and `id` (product-service uses `"products"` today; a
  future domain service would use its own collection name without any change
  here).
- Embeds a search query and delegates the KNN search to `vector-db`, within
  the caller-specified collection (`POST /search`), so callers never need the
  raw vector or to know `vector-db`'s API shape.
- Does **not** access ChromaDB directly — all vector storage/search goes
  through `vector-db`'s HTTP API.
- Does **not** contain business prompts or domain-specific text building —
  callers send ready-to-embed text and their own metadata.

Out of scope for now: reranking of search results. The `/search` endpoint is
the natural place to add a cross-encoder reranking pass later, once
`vector-db` returns a larger candidate set to re-score.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/embed` | Batch-embed a list of texts. No side effects. |
| POST | `/index` | Embed one entity's text and upsert it into a `vector-db` collection. |
| POST | `/search` | Embed a query and run KNN search via `vector-db`, within a collection. |
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
