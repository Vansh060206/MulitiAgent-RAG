import uuid
import hashlib
import logging
import math
from collections import Counter
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class BM25Ranker:
    """
    Lightweight, Python-native BM25 algorithm to rank keyword search results.
    Prevents installing heavy external packages or loading secondary model weights.
    """
    def __init__(self, corpus: List[Dict[str, Any]]):
        self.corpus = corpus
        self.corpus_size = len(corpus)
        # Calculate average document length
        self.doc_lengths = [len(doc["content"].lower().split()) for doc in corpus]
        self.avg_doc_len = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0
        
        # Build token frequencies and document frequency maps
        self.doc_freqs = []
        doc_count_with_term = {}
        
        for doc in corpus:
            words = doc["content"].lower().split()
            freq_map = Counter(words)
            self.doc_freqs.append(freq_map)
            
            for word in freq_map.keys():
                doc_count_with_term[word] = doc_count_with_term.get(word, 0) + 1
                
        # Precompute Inverse Document Frequencies (IDF)
        self.idf = {}
        for word, count in doc_count_with_term.items():
            # Standard BM25 IDF formula with smoothing parameters
            self.idf[word] = math.log((self.corpus_size - count + 0.5) / (count + 0.5) + 1.0)

    def rank(self, query: str, k1: float = 1.5, b: float = 0.75) -> List[Dict[str, Any]]:
        """Ranks the corpus against a query and returns documents sorted by BM25 score."""
        scored_docs = []
        query_words = query.lower().split()
        
        for idx, doc in enumerate(self.corpus):
            score = 0.0
            doc_len = self.doc_lengths[idx]
            freq_map = self.doc_freqs[idx]
            
            for word in query_words:
                if word not in self.idf:
                    continue
                tf = freq_map.get(word, 0)
                # BM25 frequency scaling formula
                numerator = self.idf[word] * tf * (k1 + 1)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                score += numerator / denominator
            
            # Store document along with its calculated BM25 score
            doc_copy = doc.copy()
            doc_copy["bm25_score"] = score
            scored_docs.append(doc_copy)
            
        # Sort documents in descending order of BM25 score
        return sorted(scored_docs, key=lambda x: x["bm25_score"], reverse=True)


class VectorDBService:
    """
    Qdrant Vector Database Service.
    Handles semantic search, keyword full-text indexing, and RRF hybrid retrieval.
    """
    def __init__(self, collection_name: str = "enterprise_rag"):
        self.collection_name = collection_name
        self.embeddings = EmbeddingService()
        
        # Connect to the local Qdrant container running on port 6333
        logger.info("Connecting to Qdrant client...")
        self.client = QdrantClient(url="http://localhost:6333", timeout=5.0)
        
        self._init_collection()

    def _init_collection(self):
        """Initializes the collection and payload indexes if they do not exist."""
        try:
            # Check if collection already exists
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not exists:
                logger.info(f"Collection '{self.collection_name}' not found. Creating collection...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embeddings.dimension,
                        distance=models.Distance.COSINE
                    )
                )
                
                # Create a Full-Text Index on the payload 'content' key
                # This allows Qdrant to execute rapid token matching for our keyword search
                logger.info("Creating full-text payload index on 'content'...")
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="content",
                    field_schema=models.TextIndexParams(
                        type="text",
                        tokenizer=models.TokenizerType.WORD,
                        min_token_len=2,
                        lowercase=True
                    )
                )
                logger.info(f"Collection '{self.collection_name}' initialized successfully.")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists. Reusing.")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")
            raise e

    def upsert_documents(self, chunks: List[str], metadata_list: List[Dict[str, Any]]) -> bool:
        """
        Embeds text chunks and saves them in Qdrant.
        Generates deterministic UUIDs based on chunk content hashes to prevent duplicates.
        """
        if not chunks:
            return False
            
        try:
            # Generate the vector representation for each text chunk
            vectors = self.embeddings.embed_documents(chunks)
            points = []
            
            for idx, chunk in enumerate(chunks):
                metadata = metadata_list[idx] if idx < len(metadata_list) else {}
                
                # Combine content and metadata into the payload dictionary
                payload = {
                    "content": chunk,
                    **metadata
                }
                
                # Generate a deterministic UUID based on the text hash.
                # This makes the ingestion idempotent: uploading the same document
                # multiple times overwrites old records instead of duplicating them.
                hash_object = hashlib.md5(chunk.encode("utf-8"))
                point_id = str(uuid.UUID(hash_object.hexdigest()))
                
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vectors[idx],
                        payload=payload
                    )
                )
                
            # Execute batch insert
            self.client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=points
            )
            logger.info(f"Successfully upserted {len(chunks)} points to Qdrant.")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to Qdrant: {e}")
            return False

    def search_semantic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Performs dense vector similarity search."""
        try:
            # Convert user query into coordinate vector
            query_vector = self.embeddings.embed_query(query)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            return [
                {
                    "id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"},
                    "score": hit.score
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def search_hybrid(self, query: str, limit: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Executes a hybrid search merging semantic (BGE vector) and keyword (Qdrant MatchText + BM25)
        results using Reciprocal Rank Fusion (RRF).
        """
        try:
            # 1. Fetch semantic candidates
            semantic_results = self.search_semantic(query, limit=limit * 2)
            
            # 2. Fetch keyword candidates using full-text index matching
            # MatchText searches the tokenized payload index for the query words
            keyword_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="content",
                        match=models.MatchText(text=query)
                    )
                ]
            )
            
            # Retrieve matching documents from the database
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=keyword_filter,
                limit=limit * 2,
                with_payload=True,
                with_vectors=False
            )
            
            # Format keyword matches into structured dicts
            keyword_candidates = [
                {
                    "id": point.id,
                    "content": point.payload.get("content", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "content"}
                }
                for point in scroll_result[0]
            ]
            
            # Rank keyword candidates using local BM25 scoring
            ranked_keyword = []
            if keyword_candidates:
                bm25 = BM25Ranker(keyword_candidates)
                ranked_keyword = bm25.rank(query)
                
            # 3. Reciprocal Rank Fusion (RRF) calculation
            rrf_scores: Dict[str, Dict[str, Any]] = {}
            
            # Merge semantic ranks
            for rank, hit in enumerate(semantic_results, start=1):
                doc_id = hit["id"]
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {
                        "id": doc_id,
                        "content": hit["content"],
                        "metadata": hit["metadata"],
                        "score": 0.0
                    }
                rrf_scores[doc_id]["score"] += 1.0 / (rrf_k + rank)
                
            # Merge keyword ranks
            for rank, hit in enumerate(ranked_keyword, start=1):
                doc_id = hit["id"]
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {
                        "id": doc_id,
                        "content": hit["content"],
                        "metadata": hit["metadata"],
                        "score": 0.0
                    }
                rrf_scores[doc_id]["score"] += 1.0 / (rrf_k + rank)
                
            # Sort the combined documents by their aggregated RRF score
            sorted_results = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
            return sorted_results[:limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
