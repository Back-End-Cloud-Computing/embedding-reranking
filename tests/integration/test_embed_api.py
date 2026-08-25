import httpx
import respx

from app.core.config import get_settings


async def test_embed_endpoint(api_client):
    response = await api_client.post("/embed", json={"texts": ["produto legal", "outro produto"]})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["embeddings"]) == 2
    assert data["model"] == get_settings().embedding_model_name


async def test_embed_index_success(api_client):
    base_url = get_settings().vector_db_base_url
    with respx.mock(base_url=base_url) as mock:
        mock.post("/vector_db/insert").mock(return_value=httpx.Response(200, json={"upserted": 1}))

        response = await api_client.post(
            "/embed/index",
            json={"product_id": "abc123", "text": "produto legal", "metadata": {"brand": "MarcaX"}},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "abc123"
    assert data["status"] == "indexed"


async def test_embed_index_vector_db_failure_returns_503(api_client):
    base_url = get_settings().vector_db_base_url
    with respx.mock(base_url=base_url) as mock:
        mock.post("/vector_db/insert").mock(return_value=httpx.Response(500))

        response = await api_client.post(
            "/embed/index",
            json={"product_id": "abc123", "text": "produto legal", "metadata": {}},
        )

    assert response.status_code == 503
    assert response.json()["error_type"] == "vector_db_unavailable"


async def test_search_endpoint(api_client):
    base_url = get_settings().vector_db_base_url
    with respx.mock(base_url=base_url) as mock:
        mock.post("/vector_db/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "ids": ["p1", "p2"],
                    "distances": [0.1, 0.2],
                    "metadatas": [{"brand": "A"}, {"brand": "B"}],
                    "documents": ["doc1", "doc2"],
                },
            )
        )

        response = await api_client.post("/search", json={"query": "tenis de corrida", "n_results": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["ids"] == ["p1", "p2"]
    assert data["model"] == get_settings().embedding_model_name
