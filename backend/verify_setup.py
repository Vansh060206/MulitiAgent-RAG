import os
import sys
from dotenv import load_dotenv

# Load local environment variables from a .env file if it exists
load_dotenv()

def test_imports() -> bool:
    """Verifies that all core libraries are correctly installed and importable."""
    print("\n--- Diagnostic 1: Testing Library Imports ---")
    libraries = {
        "fastapi": "FastAPI Web Framework",
        "pydantic": "Pydantic Schema Validation",
        "langgraph": "LangGraph Orchestration Engine",
        "langchain": "LangChain Core Utilities",
        "qdrant_client": "Qdrant Vector Database Client",
        "sentence_transformers": "Sentence Transformers Embeddings",
        "torch": "PyTorch ML Runtime"
    }
    
    all_passed = True
    for lib, name in libraries.items():
        try:
            __import__(lib)
            print(f"[OK] Successfully imported {lib} ({name})")
        except ImportError as e:
            print(f"[FAILED] Could not import {lib} ({name}). Error: {e}")
            all_passed = False
            
    # Test PyTorch device check (CPU vs GPU check)
    if "torch" in sys.modules:
        import torch
        device = "CUDA (GPU)" if torch.cuda.is_available() else "CPU"
        print(f"[INFO] PyTorch version: {torch.__version__}")
        print(f"[INFO] PyTorch default compute device detected: {device}")
        
    return all_passed

def test_qdrant_connection() -> bool:
    """Verifies that the Qdrant docker container is reachable and running."""
    print("\n--- Diagnostic 2: Testing Qdrant Database Connectivity ---")
    try:
        from qdrant_client import QdrantClient
        # Attempt to connect to Qdrant HTTP REST API (running on port 6333)
        client = QdrantClient(url="http://localhost:6333", timeout=5.0)
        
        # Ping the server by fetching the collections list
        collections = client.get_collections()
        print("[OK] Successfully connected to Qdrant Vector Database at http://localhost:6333")
        print(f"[INFO] Existing database collections: {collections.collections}")
        return True
    except ImportError:
        print("[FAILED] Cannot test Qdrant connection because qdrant_client is not installed.")
        return False
    except Exception as e:
        print(f"[FAILED] Could not connect to Qdrant at http://localhost:6333.")
        print(f"         Error details: {e}")
        print("         Suggestion: Make sure Docker is running and run 'docker compose up -d'")
        return False

def test_environment() -> bool:
    """Checks for required API configurations in environment variables."""
    print("\n--- Diagnostic 3: Testing Environment Variables ---")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_key:
        # Mask the key for logs safety (e.g. AI...xxxx)
        masked_key = gemini_key[:4] + "..." + gemini_key[-4:] if len(gemini_key) > 8 else "Present but short"
        print(f"[OK] GEMINI_API_KEY environment variable is configured: {masked_key}")
        return True
    else:
        print("[WARNING] GEMINI_API_KEY environment variable is NOT set.")
        print("          Suggestion: Create a 'backend/.env' or '.env' file with: GEMINI_API_KEY=your_api_key")
        return False

def main():
    print("==================================================")
    print("     Multi-Agent RAG Setup Verification Script    ")
    print("==================================================")
    
    imports_ok = test_imports()
    qdrant_ok = test_qdrant_connection()
    env_ok = test_environment()
    
    print("\n==================== SUMMARY ====================")
    if imports_ok and qdrant_ok:
        print("[SUCCESS] All core systems (imports, database) are functional!")
        if not env_ok:
            print("[NOTICE] Remember to configure your GEMINI_API_KEY before running the LLM agents.")
        sys.exit(0)
    else:
        print("[ERROR] Verification failed. Please check the errors printed above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
