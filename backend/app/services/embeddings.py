import os
import logging
from typing import List
from sentence_transformers import SentenceTransformer

# Configure logging for tracking diagnostics
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Optimized Local Embedding Service.
    Defaults to BAAI/bge-small-en-v1.5 (384-dimensions, ~130MB on disk) to save space,
    with fallbacks dynamically configurable via environment variables.
    """
    def __init__(self):
        # Allow override via environment variables, defaulting to the small, optimized model
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
        
        # BGE models require a specific prefix instruction for query vectors to activate
        # their search retrieval alignment. Passages do not require a prefix.
        self.query_prefix = "Represent this sentence for searching relevant passages: "
        
        logger.info(f"Loading local embedding model: {self.model_name}...")
        try:
            # Disable the Hugging Face symlinks warning on Windows by default if not set
            if "HF_HUB_DISABLE_SYMLINKS_WARNING" not in os.environ:
                os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
                
            self.model = SentenceTransformer(self.model_name)
            
            # Dynamically inspect the output embedding dimension from the loaded model
            # BGE-small outputs 384; BGE-base outputs 768; BGE-large outputs 1024.
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Local embedding model loaded successfully. Dimensions: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}. Error: {e}")
            raise e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of document text chunks.
        
        Inputs:
            texts: List[str] - The text passages to represent.
        Outputs:
            List[List[float]] - A list of normalized coordinate vectors.
        """
        if not texts:
            return []
            
        # normalize_embeddings=True calculates L2-normalized vectors (unit length).
        embeddings = self.model.encode(
            texts, 
            normalize_embeddings=True, 
            show_progress_bar=False
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Generates a dense vector embedding for a single user search query.
        Applies the mandatory BGE search instruction prefix.
        
        Inputs:
            query: str - The natural language query.
        Outputs:
            List[float] - A single normalized coordinate vector.
        """
        if not query:
            return []
            
        # Prepend the retrieval-specific query instruction.
        prefixed_query = f"{self.query_prefix}{query}"
        
        # Generate the single vector representation
        embedding = self.model.encode(
            prefixed_query,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding.tolist()
