from fastapi import APIRouter

from app.routes.embed import router as embed_router

api_router = APIRouter()
api_router.include_router(embed_router)

__all__ = ["api_router"]
