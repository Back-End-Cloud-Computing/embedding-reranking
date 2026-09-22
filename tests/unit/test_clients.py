import httpx
import respx

from app.clients import vector_db_client
from app.core.config import get_settings
from app.core.security import _current_token


async def test_outgoing_calls_forward_the_incoming_bearer_token():
    """The token that authenticated this request into embedding-reranking must
    be forwarded as-is to vector-db - see app.core.security.auth_headers."""
    token = _current_token.set("the-caller-token")
    try:
        settings = get_settings()
        with respx.mock(base_url=settings.vector_db_base_url) as mock:
            route = mock.post("/vector_db/insert").mock(return_value=httpx.Response(200, json={"upserted": 1}))
            await vector_db_client.insert("products", [{"id": "1"}])

        assert route.calls.last.request.headers["authorization"] == "Bearer the-caller-token"
    finally:
        _current_token.reset(token)
