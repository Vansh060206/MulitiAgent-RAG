import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """
    Application Settings and Configuration.
    Loads values from environment variables or defaults.
    """
    APP_NAME: str = "Multi-Agent Enterprise RAG Assistant"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Qdrant Database Settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "enterprise_rag")
    
    # AI Credentials
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # Upload Configurations
    UPLOAD_DIR: str = "backend/temp_uploads"
    
    class Config:
        case_sensitive = True

settings = Settings()
