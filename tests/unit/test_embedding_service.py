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
