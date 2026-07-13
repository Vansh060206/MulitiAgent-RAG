import queue
import json
import logging
import asyncio
import threading
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from app.agents.graph import app_graph
import app.agents.graph as graph_module

logger = logging.getLogger(__name__)

async def run_graph_and_stream(query: str, limit: int = 5) -> AsyncGenerator[str, None]:
    """
    Asynchronously runs the multi-agent LangGraph workflow in a background thread,
    polling for raw text tokens and node state updates, and yielding them as Server-Sent Events (SSE).
    """
    # Reset failover state tracking at start of new run
    graph_module._key_switched_during_run = False
    
    token_queue = queue.Queue()
    
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
    
    # Inject the token queue into metadata so the generate node can stream tokens
    config = {
        "metadata": {
            "token_queue": token_queue
        }
    }
    
    event_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    def run_graph_sync():
        try:
            logger.info(f"Starting graph workflow execution in background thread for query: '{query}'")
            for event in app_graph.stream(initial_state, config=config):
                # Safely put graph updates into the async queue
                asyncio.run_coroutine_threadsafe(event_queue.put({"type": "graph_event", "data": event}), loop)
            asyncio.run_coroutine_threadsafe(event_queue.put({"type": "done"}), loop)
            logger.info("Graph workflow finished successfully in background thread.")
        except Exception as e:
            logger.error(f"Graph workflow failed in background thread: {e}")
            asyncio.run_coroutine_threadsafe(event_queue.put({"type": "error", "error": str(e)}), loop)
            
    thread = threading.Thread(target=run_graph_sync)
    thread.daemon = True
    thread.start()
    
    # Poll queues and yield SSE events
    while True:
        # 1. Flush any tokens in the queue
        while not token_queue.empty():
            token = token_queue.get()
            yield f"data: {json.dumps({'event': 'token', 'data': token})}\n\n"
            
        # 2. Wait for a graph execution event
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=0.02)
            
            if event["type"] == "done":
                # Final flush of tokens
                while not token_queue.empty():
                    token = token_queue.get()
                    yield f"data: {json.dumps({'event': 'token', 'data': token})}\n\n"
                
                # Signal workflow completion
                yield f"data: {json.dumps({'event': 'done'})}\n\n"
                break
                
            elif event["type"] == "error":
                yield f"data: {json.dumps({'event': 'error', 'data': event['error']})}\n\n"
                break
                
            elif event["type"] == "graph_event":
                for node_name, node_update in event["data"].items():
                    payload = {"event": "status", "node": node_name}
                    
                    failover_notice = ""
                    if getattr(graph_module, "_key_switched_during_run", False):
                        failover_notice = " (Failed over to backup Gemini API key)"
                    
                    if node_name == "router":
                        payload["details"] = f"Router classified intent as '{node_update.get('route')}'{failover_notice}"
                        payload["route"] = node_update.get("route")
                    elif node_name == "retrieve":
                        payload["details"] = f"Retrieved {len(node_update.get('retrieved_contexts', []))} relevant passages from database"
                        payload["sources"] = node_update.get("retrieved_contexts", [])
                    elif node_name == "research":
                        payload["details"] = f"Retrieved {len(node_update.get('retrieved_contexts', []))} external web pages{failover_notice}"
                        payload["sources"] = node_update.get("retrieved_contexts", [])
                    elif node_name == "generate":
                        payload["details"] = f"Draft response completed{failover_notice}"
                        if "draft_response" in node_update:
                            payload["draft_response"] = node_update["draft_response"]
                    elif node_name == "verify":
                        score = node_update.get("verification_score", 1.0)
                        reasoning = node_update.get("verification_reasoning", "")
                        payload["details"] = f"Hallucination audit score: {score:.2f}{failover_notice}"
                        payload["verification"] = {
                            "score": score,
                            "reasoning": reasoning
                        }
                    
                    yield f"data: {json.dumps(payload)}\n\n"
        except asyncio.TimeoutError:
            # No graph event in this tick, continue loop to keep polling tokens
            continue
