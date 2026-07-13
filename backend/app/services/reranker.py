import os
import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class RerankerService:
    """
    Optimized Local Reranking Service using Sentence Transformers CrossEncoder.
    Defaults to BAAI/bge-reranker-base (~270MB on disk) for local, high-precision ranking.
    """
    def __init__(self):
        # Enable override via environment variable
        self.model_name = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-base")
        self.enabled = os.getenv("RERANKER_ENABLED", "True").lower() in ("true", "1", "t")
        
        if not self.enabled:
            logger.info("Local reranking is disabled via environment variables.")
            self.model = None
            return

        logger.info(f"Loading local reranker model: {self.model_name}...")
        try:
            self.model = CrossEncoder(self.model_name)
            logger.info("Local reranker model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load reranker model {self.model_name}. Error: {e}")
            logger.warning("Reranker will fallback to bypass mode (returning unranked documents).")
            self.model = None

    def rerank(self, query: str, documents: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate documents against a search query.
        
        Inputs:
            query: str - The original search query.
            documents: List[Dict[str, Any]] - Retrieved document chunks from Qdrant/hybrid search.
            limit: int - Number of top reranked documents to return.
        Outputs:
            List[Dict[str, Any]] - The top-K reranked documents.
        """
        if not documents:
            return []
            
        if not self.model or not self.enabled:
            logger.info("Reranker bypassed (not loaded or disabled). Returning top-K as-is.")
            return documents[:limit]

        try:
            # CrossEncoder expects a list of [query, text] pairs
            pairs = [[query, doc.get("content", "")] for doc in documents]
            scores = self.model.predict(pairs)
            
            # Map scores back to documents
            scored_docs = []
            for idx, doc in enumerate(documents):
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = float(scores[idx])
                scored_docs.append(doc_copy)
                
            # Sort in descending order of rerank score
            sorted_docs = sorted(scored_docs, key=lambda x: x["rerank_score"], reverse=True)
            logger.info(f"Successfully reranked {len(documents)} documents. Top score: {sorted_docs[0]['rerank_score']:.4f}")
            return sorted_docs[:limit]
        except Exception as e:
            logger.error(f"Error during reranking process: {e}")
            return documents[:limit]
