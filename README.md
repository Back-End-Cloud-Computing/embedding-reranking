# embedding-reranking

Embedding generation microservice for the GANJJ e-commerce platform, built with
**FastAPI** + `sentence-transformers`. It is the only service allowed to call
`vector-db` for indexing or searching product vectors — `product-service`
never talks to `vector-db` directly for those operations.

## Scope

- Generates text embeddings in batch, off the event loop (`asyncio.to_thread`),
  using a free/open-source multilingual model
  (`paraphrase-multilingual-MiniLM-L12-v2` by default), suitable for Portuguese.
- Indexes a product's embedding into `vector-db` on behalf of `product-service`
  (`POST /embed/index`).
- Embeds a search query and delegates the KNN search to `vector-db`
  (`POST /search`), so `product-service` never needs the raw vector or to know
  `vector-db`'s API shape.
- Does **not** access ChromaDB directly — all vector storage/search goes
  through `vector-db`'s HTTP API.
- Does **not** contain business prompts or product-specific text building —
  callers send ready-to-embed text.

Out of scope for now: reranking of search results. The `/search` endpoint is
the natural place to add a cross-encoder reranking pass later, once
`vector-db` returns a larger candidate set to re-score.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/embed` | Batch-embed a list of texts. No side effects. |
| POST | `/embed/index` | Embed one product's text and upsert it into `vector-db`. |
| POST | `/search` | Embed a query and run KNN search via `vector-db`. |
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
