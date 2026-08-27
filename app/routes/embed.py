import logging

from fastapi import APIRouter

from app.clients import vector_db_client
from app.core.config import get_settings
from app.schemas.embed import (
    EmbedRequest,
    EmbedResponse,
    IndexRequest,
    IndexResponse,
    RankedPassage,
    RerankRequest,
    RerankResponse,
)
from app.services import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["embedding"])


@router.post("/embed", response_model=EmbedResponse)
async def embed(payload: EmbedRequest) -> EmbedResponse:
    """Pure batch embedding generation. No side effects: nothing is indexed."""
    embeddings = await embedding_service.generate_embeddings(payload.texts)
    return EmbedResponse(embeddings=embeddings, model=get_settings().embedding_model_name, count=len(payload.texts))


@router.post("/index", response_model=IndexResponse)
async def index(payload: IndexRequest) -> IndexResponse:
    """Generates the embedding for one entity and (re)indexes it into the
    vector-db, under the caller-specified collection. Generic across entity
    types: the caller (product-service today, any future domain service
    tomorrow) just states which collection its data belongs to.

    Any existing vector under the same id is deleted first, so re-indexing an
    entity (or a retried call) never leaves duplicate rows behind - Chroma's
    own upsert already replaces same-id rows in place, but this makes that
    guarantee explicit and independent of insert-path semantics.

    This is the only path that indexes a vector: the caller is expected to
    retry on failure, so any downstream error here propagates instead of
    being swallowed.
    """
    await vector_db_client.delete(collection_name=payload.collection_name, ids=[payload.id])

    embeddings = await embedding_service.generate_embeddings([payload.text])
    await vector_db_client.insert(
        collection_name=payload.collection_name,
        items=[
            {
                "id": payload.id,
                "embedding": embeddings[0],
                "metadata": payload.metadata,
                "document": payload.text,
            }
        ],
    )
    logger.info("Indexed '%s' into vector-db collection '%s'", payload.id, payload.collection_name)
    return IndexResponse(
        id=payload.id,
        collection_name=payload.collection_name,
        status="indexed",
        model=get_settings().embedding_model_name,
    )


@router.post("/rerank", response_model=RerankResponse)
async def rerank(payload: RerankRequest) -> RerankResponse:
    """Reorders the caller-supplied passages by relevance to `query`. Pure
    function: the caller (typically after searching its own vector-db
    collection) supplies the candidate passages directly - this endpoint has
    no vector-db or collection knowledge."""
    ranked = await embedding_service.rerank_passages(payload.query, payload.passages)
    results = [RankedPassage(passage=passage, score=score, index=index) for index, passage, score in ranked]
    return RerankResponse(results=results, model=get_settings().embedding_model_name, query=payload.query)
