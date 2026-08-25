from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import EmbeddingGenerationError, VectorDbUnavailableError
from app.core.logging import configure_logging
from app.routes import api_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Embedding generation service: batch text embeddings and product indexing into vector-db.",
        version="1.0.0",
    )

    application.include_router(api_router)

    @application.exception_handler(EmbeddingGenerationError)
    async def embedding_error_handler(request: Request, exc: EmbeddingGenerationError) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": str(exc), "error_type": "embedding_generation_error"}
        )

    @application.exception_handler(VectorDbUnavailableError)
    async def vector_db_error_handler(request: Request, exc: VectorDbUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc), "error_type": "vector_db_unavailable"})

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
