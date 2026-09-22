import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import CurrentUser, get_current_user
from app.services import embedding_service

FAKE_USER = CurrentUser(id="11111111-1111-1111-1111-111111111111", email="teste@ganjj.com", role="CLIENTE")


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
    """Authenticated API client: overrides `get_current_user` so existing
    tests don't need to carry a real token. Auth enforcement itself is
    covered separately in `tests/integration/test_auth.py`, against the
    real dependency."""
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_current_user, None)
