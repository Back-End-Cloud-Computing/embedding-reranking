import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import VectorDbUnavailableError

logger = logging.getLogger(__name__)


async def insert(collection_name: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            base_url=settings.vector_db_base_url, timeout=settings.vector_db_timeout_seconds
        ) as client:
            response = await client.post(
                "/vector_db/insert", json={"collection_name": collection_name, "items": items}
            )
            response.raise_for_status()
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
            response = await client.post(
                "/vector_db/delete", json={"collection_name": collection_name, "ids": ids}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.error("vector-db delete failed: %s", exc)
        raise VectorDbUnavailableError(f"vector-db delete failed: {exc}") from exc
