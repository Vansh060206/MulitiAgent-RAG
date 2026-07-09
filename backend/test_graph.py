import os
import sys
import logging
import time
from dotenv import load_dotenv

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load env variables immediately
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from langchain_core.messages import HumanMessage
from app.agents.graph import app_graph

def run_test_query(query: str):
    print("\n" + "=" * 60)
    print(f"TESTING QUERY: {query}")
    print("=" * 60)
    
    # Define initial state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "retrieved_contexts": [],
        "draft_response": "",
        "route": "",
        "verification_score": 0.0,
        "verification_reasoning": "",
        "verification_attempts": 0
    }
    
    # Run the graph and print trace steps
    try:
        events = app_graph.stream(initial_state)
        final_state = None
        
        for event in events:
            for node_name, state in event.items():
                print(f"\n>>> Step: {node_name}")
                if "route" in state:
                    print(f"    Route: {state['route']}")
                if "verification_score" in state:
                    print(f"    Verify Score: {state['verification_score']}")
                    print(f"    Verify Reasoning: {state['verification_reasoning']}")
                if "draft_response" in state and node_name == "generate":
                    print(f"    Draft Response Preview: {state['draft_response'][:150]}...")
                final_state = state
                
        print("\n" + "-" * 40)
        print("FINAL RESULTS")
        print("-" * 40)
        if final_state:
            print(f"Final Route: {final_state.get('route')}")
            print(f"Attempts: {final_state.get('verification_attempts')}")
            print(f"Final Answer:\n{final_state.get('draft_response')}")
        else:
            print("No state returned.")
            
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")

def main():
    # Load .env file
    load_dotenv()
    
    # Query 1: Routing to General Conversation (generate)
    run_test_query("Hello there! Who are you and what can you help me with?")
    
    print("\n[INFO] Sleeping for 15 seconds to avoid API rate limits...")
    time.sleep(15)
    
    # Query 2: Routing to Web Research (research)
    run_test_query("What is the latest version of Next.js and its main new features in 2026?")
    
    print("\n[INFO] Sleeping for 15 seconds to avoid API rate limits...")
    time.sleep(15)
    
    # Query 3: Routing to Local Retrieval (retrieve)
    # This will fetch Qdrant results (which might contain our dummy pdf results or financial data from test_vector_db)
    run_test_query("How much money did we make in total Q3 2025?")

if __name__ == "__main__":
    main()
