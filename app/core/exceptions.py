class EmbeddingRerankingError(Exception):
    """Base exception for the embedding-reranking service domain."""


class EmbeddingGenerationError(EmbeddingRerankingError):
    """Raised when embedding generation fails."""


class VectorDbUnavailableError(EmbeddingRerankingError):
    """Raised when the vector-db service cannot be reached or returns an error."""


class AuthenticationError(EmbeddingRerankingError):
    """Raised when the incoming request's bearer token is missing, malformed, or
    fails local verification against the authorization service's public key."""
