from fastapi import APIRouter
from app.api.endpoints import ingest, chat

api_router = APIRouter()

# Register endpoint sub-routers under their respective sub-paths
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(chat.router, prefix="/chat", tags=["Retrieval Chat"])
