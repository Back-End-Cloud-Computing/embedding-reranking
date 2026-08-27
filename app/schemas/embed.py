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


class RerankRequest(BaseModel):
    """Reorders a caller-supplied list of passages by relevance to `query`.

    Pure function: takes no collection/vector-db knowledge, so it works on
    candidates retrieved from anywhere (typically the caller's own
    vector-db search results)."""

    query: str = Field(..., min_length=1)
    passages: list[str] = Field(..., min_length=1)


class RankedPassage(BaseModel):
    passage: str = Field(..., description="The passage text")
    score: float = Field(..., description="Cosine similarity to the query, in [-1, 1]")
    index: int = Field(..., description="Position of this passage in the original `passages` list")


class RerankResponse(BaseModel):
    results: list[RankedPassage] = Field(..., description="Passages ranked from most to least relevant")
    model: str
    query: str
