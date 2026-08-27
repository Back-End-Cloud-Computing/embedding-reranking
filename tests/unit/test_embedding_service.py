import pytest

from app.core.exceptions import EmbeddingGenerationError
from app.services import embedding_service


async def test_generate_embeddings_batch():
    embeddings = await embedding_service.generate_embeddings(["hello", "world"])
    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]


async def test_generate_embeddings_empty_list():
    assert await embedding_service.generate_embeddings([]) == []


async def test_generate_embeddings_wraps_backend_errors(monkeypatch):
    async def broken_get_embedding_model():
        raise RuntimeError("model failed to load")

    monkeypatch.setattr(embedding_service, "get_embedding_model", broken_get_embedding_model)

    with pytest.raises(EmbeddingGenerationError):
        await embedding_service.generate_embeddings(["hello"])


async def test_rerank_passages_orders_by_cosine_similarity(monkeypatch):
    """The autouse fixture's fake model returns an identical vector for every
    text, which can't exercise real ranking - this test uses its own fake
    model with distinguishable per-text vectors instead."""
    import numpy as np

    vectors = {
        "query": [1.0, 0.0],
        "passagem parecida": [0.9, 0.1],
        "passagem diferente": [0.0, 1.0],
    }

    class _DistinctFakeModel:
        def encode(self, texts, normalize_embeddings: bool = True):
            arr = np.array([vectors[text] for text in texts])
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            return arr / norms

    async def fake_get_embedding_model():
        return _DistinctFakeModel()

    monkeypatch.setattr(embedding_service, "get_embedding_model", fake_get_embedding_model)

    ranked = await embedding_service.rerank_passages("query", ["passagem diferente", "passagem parecida"])

    assert [passage for _, passage, _ in ranked] == ["passagem parecida", "passagem diferente"]
    assert ranked[0][2] > ranked[1][2]
    # original indices are preserved even though the order changed
    assert {index for index, _, _ in ranked} == {0, 1}
