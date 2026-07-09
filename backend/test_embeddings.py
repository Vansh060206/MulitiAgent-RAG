import sys
import logging
from app.services.embeddings import EmbeddingService

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_embedding_service():
    print("==================================================")
    print("      Testing Optimized Embedding Service         ")
    print("==================================================")
    
    try:
        # Initialize the embedding service
        service = EmbeddingService()
        
        # Test document embedding
        test_docs = [
            "This is a test passage about deep learning.",
            "FastAPI is a modern web framework for Python."
        ]
        
        print(f"\n[INFO] Expected dimension from loaded model: {service.dimension}")
        
        print("\n[TEST] Embedding document list...")
        doc_embeddings = service.embed_documents(test_docs)
        
        # Dynamic assertions using the inspected dimensions property
        assert len(doc_embeddings) == len(test_docs), "Output count does not match input count"
        assert len(doc_embeddings[0]) == service.dimension, f"Expected {service.dimension} dimensions, got {len(doc_embeddings[0])}"
        print(f"[OK] Successfully embedded {len(test_docs)} documents.")
        print(f"[OK] Vector dimensions check: {len(doc_embeddings[0])} dimensions.")
        print(f"[INFO] Sample vector (first 5 dimensions): {doc_embeddings[0][:5]}...")
        
        # Test query embedding
        test_query = "What is FastAPI?"
        print("\n[TEST] Embedding query...")
        query_embedding = service.embed_query(test_query)
        
        # Assertions
        assert len(query_embedding) == service.dimension, f"Expected {service.dimension} dimensions, got {len(query_embedding)}"
        print(f"[OK] Successfully embedded search query.")
        print(f"[INFO] Query vector (first 5 dimensions): {query_embedding[:5]}...")
        
        print("\n[SUCCESS] Optimized embedding service is fully functional!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[FAILED] Embedding service test failed. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_embedding_service()
