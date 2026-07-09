import os
import sys
import time
import subprocess
import urllib.request
import requests

def download_sample_pdf(url: str, dest_path: str):
    print(f"[INFO] Downloading sample PDF from {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        with open(dest_path, 'wb') as out_file:
            out_file.write(response.read())

def run_integration_test():
    print("==================================================")
    print("      Testing FastAPI Gateway Integration         ")
    print("==================================================")
    
    server_process = None
    local_pdf = "backend/sample_api_test.pdf"
    sample_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    log_file_path = "backend/server_test.log"
    log_file = None
    
    try:
        # 1. Download the sample PDF
        download_sample_pdf(sample_pdf_url, local_pdf)
        
        # 2. Start the FastAPI backend server using Uvicorn in the background.
        # We start it on port 8000 from the backend folder.
        print("\n[INFO] Starting Uvicorn backend server in the background...")
        uvicorn_bin = os.path.join(".venv", "Scripts", "uvicorn")
        
        # Open a local log file to pipe output.
        # This prevents Popen pipe buffer deadlocks (when buffers exceed 64KB).
        log_file = open(log_file_path, "w", encoding="utf-8")
        
        # Start uvicorn. Note: we run Uvicorn targeting 'app.main:app'
        server_process = subprocess.Popen(
            [uvicorn_bin, "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd="backend",
            stdout=log_file,
            stderr=log_file,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        
        # Wait a few seconds for the Uvicorn server to initialize the model and connect to Qdrant
        print("[INFO] Waiting for Uvicorn server to boot (loading model & database links)...")
        time.sleep(20)
        
        # Check if the server crashed on boot
        if server_process.poll() is not None:
            print("[FAILED] Server failed to start. Reviewing log file...")
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    print(f"[SERVER LOGS]:\n{f.read()}")
            sys.exit(1)
            
        print("[OK] Server process started.")
        
        # 3. Test HTTP Root Health Check
        health_url = "http://127.0.0.1:8000/"
        print(f"\n[TEST] Querying health check at: {health_url}")
        resp = requests.get(health_url)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[OK] Health check response: {resp.json()}")
        
        # 4. Test Ingestion Upload Route
        upload_url = "http://127.0.0.1:8000/api/ingest/upload"
        print(f"\n[TEST] Uploading PDF via POST: {upload_url}")
        with open(local_pdf, "rb") as f:
            files = {"file": (os.path.basename(local_pdf), f, "application/pdf")}
            upload_resp = requests.post(upload_url, files=files)
            
        assert upload_resp.status_code == 201, f"Expected 201, got {upload_resp.status_code}"
        print(f"[OK] Upload Response: {upload_resp.json()}")
        
        # 5. Test Chat Retrieval Route
        retrieve_url = "http://127.0.0.1:8000/api/chat/retrieve"
        payload = {
            "query": "dummy PDF file text matches",
            "limit": 3
        }
        print(f"\n[TEST] Retrieving context via POST: {retrieve_url}")
        retrieve_resp = requests.post(retrieve_url, json=payload)
        
        assert retrieve_resp.status_code == 200, f"Expected 200, got {retrieve_resp.status_code}"
        results = retrieve_resp.json()
        print(f"[OK] Retrieval Response: {results}")
        
        assert len(results["results"]) > 0, "No results returned"
        
        # 6. Test Chat Ask Endpoint (Multi-Agent RAG execution)
        ask_url = "http://127.0.0.1:8000/api/chat/ask"
        ask_payload = {
            "query": "What is in the uploaded dummy PDF file matches?",
            "limit": 3
        }
        print(f"\n[TEST] Asking Multi-Agent RAG via POST: {ask_url}")
        ask_resp = requests.post(ask_url, json=ask_payload)
        
        assert ask_resp.status_code == 200, f"Expected 200, got {ask_resp.status_code}"
        ask_results = ask_resp.json()
        print(f"[OK] Ask Response: {ask_results}")
        
        assert "answer" in ask_results, "No answer returned"
        assert len(ask_results["trace"]) > 0, "No execution trace returned"
        print("\n[SUCCESS] FastAPI Endpoints & Multi-Agent RAG Integration are 100% verified!")
        
    except Exception as e:
        print(f"\n[FAILED] Integration test failed. Error: {e}")
        # Print server logs on failure
        if log_file:
            log_file.close()
        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                print(f"[SERVER LOGS]:\n{f.read()}")
        sys.exit(1)
        
    finally:
        # Shutdown the uvicorn background process
        if server_process and server_process.poll() is None:
            print("\n[INFO] Terminating Uvicorn backend server...")
            server_process.terminate()
            server_process.wait()
            print("[OK] Server shutdown complete.")
            
        # Close file handles
        if log_file and not log_file.closed:
            log_file.close()
            
        # Clean up local test file
        if os.path.exists(local_pdf):
            os.remove(local_pdf)
            print("[INFO] Cleaned up local test PDF file.")
            
        # Clean up local log file
        if os.path.exists(log_file_path):
            try:
                os.remove(log_file_path)
                print("[INFO] Cleaned up local test server log.")
            except PermissionError:
                print("[WARNING] Could not delete log file due to Windows filesystem lock. Skipping.")

if __name__ == "__main__":
    run_integration_test()
