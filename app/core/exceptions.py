class EmbeddingRerankingError(Exception):
    """Base exception for the embedding-reranking service domain."""


class EmbeddingGenerationError(EmbeddingRerankingError):
    """Raised when embedding generation fails."""


class VectorDbUnavailableError(EmbeddingRerankingError):
    """Raised when the vector-db service cannot be reached or returns an error."""
