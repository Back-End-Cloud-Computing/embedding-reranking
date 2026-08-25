import logging

from fastapi import APIRouter

from app.clients import vector_db_client
from app.core.config import get_settings
from app.schemas.embed import (
    EmbedIndexRequest,
    EmbedIndexResponse,
    EmbedRequest,
    EmbedResponse,
    SearchRequest,
    SearchResponse,
)
from app.services import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["embedding"])


@router.post("/embed", response_model=EmbedResponse)
async def embed(payload: EmbedRequest) -> EmbedResponse:
    """Pure batch embedding generation. No side effects: nothing is indexed."""
    embeddings = await embedding_service.generate_embeddings(payload.texts)
    return EmbedResponse(embeddings=embeddings, model=get_settings().embedding_model_name, count=len(payload.texts))


@router.post("/embed/index", response_model=EmbedIndexResponse)
async def embed_index(payload: EmbedIndexRequest) -> EmbedIndexResponse:
    """Generates the embedding for a product and indexes it into the vector-db.

    This is the only path that indexes a product's vector: the caller (the
    product-service) is expected to retry on failure, so any downstream error
    here propagates instead of being swallowed.
    """
    embeddings = await embedding_service.generate_embeddings([payload.text])
    await vector_db_client.insert(
        [
            {
                "product_id": payload.product_id,
                "embedding": embeddings[0],
                "metadata": payload.metadata,
                "document": payload.text,
            }
        ]
    )
    logger.info("Indexed product '%s' into vector-db", payload.product_id)
    return EmbedIndexResponse(product_id=payload.product_id, status="indexed", model=get_settings().embedding_model_name)


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest) -> SearchResponse:
    """Embeds the query text and delegates the KNN search to the vector-db."""
    embeddings = await embedding_service.generate_embeddings([payload.query])
    result = await vector_db_client.search(embeddings[0], n_results=payload.n_results, where=payload.where)
    return SearchResponse(
        ids=result.get("ids", []),
        distances=result.get("distances", []),
        metadatas=result.get("metadatas", []),
        documents=result.get("documents", []),
        model=get_settings().embedding_model_name,
    )
