import requests
import json

def test_running_ask():
    url = "http://127.0.0.1:8000/api/chat/ask"
    payload = {
        "query": "What is in the uploaded dummy PDF file matches?",
        "limit": 3
    }
    
    print(f"Sending POST request to: {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Raw Response: {json.dumps(results, indent=2)}")
            print("\n" + "=" * 60)
            print("AGENT RESPONSE:")
            print("=" * 60)
            print(results.get("answer"))
            
            print("\n" + "=" * 60)
            print("AGENT EXECUTION TRACE:")
            print("=" * 60)
            for idx, step in enumerate(results.get("trace", []), 1):
                print(f"{idx}. Node: {step['node']}")
                print(f"   Details: {step['details']}")
                
            print("\n" + "=" * 60)
            print(f"SOURCES RETRIEVED ({len(results.get('sources', []))}):")
            print("=" * 60)
            for src in results.get("sources", []):
                print(f"- Source Type: {src.get('source')}, Doc: {src.get('doc_name')} (Page/URL: {src.get('page') or src.get('url')})")
            
            print("\n" + "=" * 60)
            print(f"VERIFICATION SCORE: {results.get('verification_score')}")
            print(f"Reasoning: {results.get('verification_reasoning')}")
            print("=" * 60)
        else:
            print(f"Failed response: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_running_ask()
