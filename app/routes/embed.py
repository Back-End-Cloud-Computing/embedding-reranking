import logging

from fastapi import APIRouter

from app.clients import vector_db_client
from app.core.config import get_settings
from app.schemas.embed import (
    EmbedRequest,
    EmbedResponse,
    IndexRequest,
    IndexResponse,
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


@router.post("/index", response_model=IndexResponse)
async def index(payload: IndexRequest) -> IndexResponse:
    """Generates the embedding for one entity and indexes it into the vector-db,
    under the caller-specified collection. Generic across entity types: the
    caller (product-service today, any future domain service tomorrow) just
    states which collection its data belongs to.

    This is the only path that indexes a vector: the caller is expected to
    retry on failure, so any downstream error here propagates instead of
    being swallowed.
    """
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


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest) -> SearchResponse:
    """Embeds the query text and delegates the KNN search to the vector-db,
    within the caller-specified collection."""
    embeddings = await embedding_service.generate_embeddings([payload.query])
    result = await vector_db_client.search(
        collection_name=payload.collection_name,
        embedding=embeddings[0],
        n_results=payload.n_results,
        where=payload.where,
    )
    return SearchResponse(
        ids=result.get("ids", []),
        distances=result.get("distances", []),
        metadatas=result.get("metadatas", []),
        documents=result.get("documents", []),
        model=get_settings().embedding_model_name,
    )
