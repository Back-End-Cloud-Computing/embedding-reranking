import asyncio
import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_model_lock = asyncio.Lock()


async def get_embedding_model() -> SentenceTransformer:
    """Lazily load the embedding model once per process (CPU-bound, so it runs
    in a worker thread to avoid blocking the event loop)."""
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                settings = get_settings()
                logger.info("Loading embedding model '%s'", settings.embedding_model_name)
                _model = await asyncio.to_thread(
                    SentenceTransformer,
                    settings.embedding_model_name,
                    device=settings.embedding_device,
                )
    return _model


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Encodes a batch of texts in a single worker-thread call, keeping the
    event loop free while the (CPU-bound) model runs."""
    if not texts:
        return []
    try:
        model = await get_embedding_model()
        embeddings = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
        logger.info("Generated %d embedding(s) with model '%s'", len(texts), get_settings().embedding_model_name)
        return embeddings.tolist()
    except Exception as exc:  # noqa: BLE001 - normalize any backend failure
        logger.error("Embedding generation failed for %d text(s): %s", len(texts), exc)
        raise EmbeddingGenerationError(f"Failed to generate embeddings: {exc}") from exc


async def rerank_passages(query: str, passages: list[str]) -> list[tuple[int, str, float]]:
    """Reorders `passages` by relevance to `query` using cosine similarity
    between their embeddings (from the same bi-encoder model used for
    indexing - no separate cross-encoder model to load/serve).

    Returns (original_index, passage, score) tuples sorted by score descending.
    """
    vectors = await generate_embeddings([query, *passages])
    query_vector = np.array(vectors[0])
    passage_vectors = np.array(vectors[1:])
    # generate_embeddings() already L2-normalizes, so the dot product is the
    # cosine similarity directly.
    scores = passage_vectors @ query_vector

    ranked_indices = sorted(range(len(passages)), key=lambda i: scores[i], reverse=True)
    return [(i, passages[i], float(scores[i])) for i in ranked_indices]
