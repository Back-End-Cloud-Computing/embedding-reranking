import json

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


async def test_index_deletes_before_inserting_then_succeeds(api_client):
    """Dedup guarantee: any existing vector under the same id is removed first,
    so re-indexing (or a retried call) never leaves duplicate rows behind."""
    base_url = get_settings().vector_db_base_url
    with respx.mock(base_url=base_url) as mock:
        delete_route = mock.post("/vector_db/delete").mock(return_value=httpx.Response(200, json={"deleted": True}))
        insert_route = mock.post("/vector_db/insert").mock(return_value=httpx.Response(200, json={"upserted": 1}))

        response = await api_client.post(
            "/index",
            json={
                "collection_name": "products",
                "id": "abc123",
                "text": "produto legal",
                "metadata": {"brand": "MarcaX"},
            },
        )

        assert delete_route.called
        assert insert_route.called
        # Delete must run before insert, not after (otherwise it would wipe
        # the row it just inserted).
        called_paths = [call.request.url.path for call in mock.calls]
        assert called_paths == ["/vector_db/delete", "/vector_db/insert"]
        delete_body = json.loads(delete_route.calls.last.request.content)
        assert delete_body == {"collection_name": "products", "ids": ["abc123"]}

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "abc123"
    assert data["collection_name"] == "products"
    assert data["status"] == "indexed"


async def test_index_delete_failure_returns_503_and_skips_insert(api_client):
    base_url = get_settings().vector_db_base_url
    with respx.mock(base_url=base_url, assert_all_called=False) as mock:
        mock.post("/vector_db/delete").mock(return_value=httpx.Response(500))
        insert_route = mock.post("/vector_db/insert").mock(return_value=httpx.Response(200, json={"upserted": 1}))

        response = await api_client.post(
            "/index",
            json={"collection_name": "products", "id": "abc123", "text": "produto legal", "metadata": {}},
        )

    assert response.status_code == 503
    assert response.json()["error_type"] == "vector_db_unavailable"
    assert not insert_route.called


async def test_index_insert_failure_returns_503(api_client):
    base_url = get_settings().vector_db_base_url
    with respx.mock(base_url=base_url) as mock:
        mock.post("/vector_db/delete").mock(return_value=httpx.Response(200, json={"deleted": True}))
        mock.post("/vector_db/insert").mock(return_value=httpx.Response(500))

        response = await api_client.post(
            "/index",
            json={"collection_name": "products", "id": "abc123", "text": "produto legal", "metadata": {}},
        )

    assert response.status_code == 503
    assert response.json()["error_type"] == "vector_db_unavailable"


async def test_rerank_endpoint(api_client):
    response = await api_client.post(
        "/rerank",
        json={"query": "tenis de corrida", "passages": ["passagem a", "passagem b"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "tenis de corrida"
    assert data["model"] == get_settings().embedding_model_name
    assert {item["passage"] for item in data["results"]} == {"passagem a", "passagem b"}
    assert {item["index"] for item in data["results"]} == {0, 1}
