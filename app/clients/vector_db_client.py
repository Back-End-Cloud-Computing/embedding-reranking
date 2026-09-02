import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import VectorDbUnavailableError
from app.core.http_retry import post_with_retry

logger = logging.getLogger(__name__)


async def insert(collection_name: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            base_url=settings.vector_db_base_url, timeout=settings.vector_db_timeout_seconds
        ) as client:
            response = await post_with_retry(
                client, "/vector_db/insert", {"collection_name": collection_name, "items": items}
            )
            return response.json()
    except httpx.HTTPError as exc:
        logger.error("vector-db insert failed: %s", exc)
        raise VectorDbUnavailableError(f"vector-db insert failed: {exc}") from exc


async def delete(collection_name: str, ids: list[str]) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            base_url=settings.vector_db_base_url, timeout=settings.vector_db_timeout_seconds
        ) as client:
            response = await post_with_retry(client, "/vector_db/delete", {"collection_name": collection_name, "ids": ids})
            return response.json()
    except httpx.HTTPError as exc:
        logger.error("vector-db delete failed: %s", exc)
        raise VectorDbUnavailableError(f"vector-db delete failed: {exc}") from exc
