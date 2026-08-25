import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.services import embedding_service


class _FakeEmbeddingModel:
    def encode(self, texts, normalize_embeddings: bool = True):
        return np.array([[0.1, 0.2, 0.3] for _ in texts])


@pytest.fixture(autouse=True)
def patch_embedding_model(monkeypatch):
    """Keeps tests offline: never actually loads sentence-transformers weights."""

    async def fake_get_embedding_model() -> _FakeEmbeddingModel:
        return _FakeEmbeddingModel()

    monkeypatch.setattr(embedding_service, "get_embedding_model", fake_get_embedding_model)


@pytest_asyncio.fixture
async def api_client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
