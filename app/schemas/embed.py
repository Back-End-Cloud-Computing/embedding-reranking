from typing import Any

from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    count: int


class IndexRequest(BaseModel):
    collection_name: str = Field(..., min_length=1, description="Vector-db collection this entity is indexed into.")
    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexResponse(BaseModel):
    id: str
    collection_name: str
    status: str
    model: str


class SearchRequest(BaseModel):
    collection_name: str = Field(..., min_length=1, description="Vector-db collection to search in.")
    query: str = Field(..., min_length=1)
    n_results: int = Field(default=10, ge=1, le=100)
    where: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    ids: list[str]
    distances: list[float]
    metadatas: list[dict[str, Any]]
    documents: list[str]
    model: str
