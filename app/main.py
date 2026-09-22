from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, EmbeddingGenerationError, VectorDbUnavailableError
from app.core.logging import configure_logging
from app.core.security import get_current_user, load_public_key
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_public_key()
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Embedding generation service: batch text embeddings and product indexing into vector-db.",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.include_router(api_router, dependencies=[Depends(get_current_user)])

    @application.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc), "error_type": "authentication_error"})

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
