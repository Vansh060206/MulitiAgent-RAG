from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

# Initialize the core FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI gateway managing multi-agent RAG pipelines."
)

# Configure CORS Middleware
# Allows the frontend (Next.js running on port 3000) to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Explicit origins are safer than "*"
    allow_credentials=True,
    allow_methods=["*"],  # Allow all standard verbs: GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allow all custom HTTP headers (such as Content-Type)
)

# Mount the unified API Router containing ingest and chat endpoints
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/", tags=["Root"])
async def read_root():
    """Root health check endpoint."""
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs"
    }
