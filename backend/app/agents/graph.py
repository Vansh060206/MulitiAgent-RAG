import os
import json
import logging
from typing import Dict, Any, List
from tavily import TavilyClient

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.services.vector_db import VectorDBService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize services
vector_db = VectorDBService(collection_name=settings.COLLECTION_NAME)

# Set API Keys explicitly if needed
if settings.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

def get_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Helper function to initialize the Gemini LLM."""
    # Use gemini-2.5-flash as default, falling back if needed
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=settings.GEMINI_API_KEY
    )

# --- Node Implementations ---

def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the user's latest query and decides the optimal routing path:
    - 'retrieve' for questions needing local document context.
    - 'research' for questions needing real-time web search.
    - 'generate' for general conversation/greetings.
    """
    logger.info("--- NODE: Router ---")
    
    # Get the latest user message
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    if not user_messages:
        return {"route": "generate", "query": "", "verification_attempts": 0, "retrieved_contexts": []}
    
    latest_query = user_messages[-1].content
    llm = get_llm(temperature=0.0)
    
    prompt = f"""You are an advanced query router for an enterprise RAG assistant.
Analyze the user's request and classify it into one of these three categories:
1. "retrieve": The request is looking for proprietary enterprise knowledge, uploaded reports, PDFs, policies, internal financial figures, or documentation.
2. "research": The request is looking for recent events, news, general real-world facts, programming libraries documentation, public statistics, or details that change over time.
3. "generate": The request is general conversation, greeting, a request to summarize previous messages, or a generic reasoning task that doesn't need external data lookup.

Return ONLY a JSON object with:
- "route": One of the three strings: "retrieve", "research", or "generate"
- "reason": A very brief explanation of your routing choice.

User Request: "{latest_query}"
JSON Output:"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        # Clean up JSON formatting if any
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(content)
        route = parsed.get("route", "generate")
        logger.info(f"Router decided route: {route} | Reason: {parsed.get('reason', '')}")
    except Exception as e:
        logger.error(f"Router node failed: {e}. Defaulting to 'retrieve'")
        route = "retrieve"
        
    return {
        "route": route,
        "query": latest_query,
        "verification_attempts": 0,
        "retrieved_contexts": []
    }


def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """
    Queries Qdrant to fetch the most relevant local documents.
    """
    logger.info("--- NODE: Retrieval ---")
    query = state["query"]
    
    try:
        logger.info(f"Retrieving context for query: {query}")
        results = vector_db.search_hybrid(query=query, limit=5)
        
        formatted_contexts = []
        for hit in results:
            formatted_contexts.append({
                "source": "local",
                "doc_name": hit["metadata"].get("doc_name", "Unknown"),
                "page": hit["metadata"].get("page_number", 1),
                "content": hit["content"]
            })
            
        logger.info(f"Retrieved {len(formatted_contexts)} chunks from local vector store.")
    except Exception as e:
        logger.error(f"Retrieval node failed: {e}")
        formatted_contexts = []
        
    return {
        "retrieved_contexts": formatted_contexts,
        "route": "generate"
    }


def research_node(state: AgentState) -> Dict[str, Any]:
    """
    Uses the Tavily client to retrieve web search context.
    """
    logger.info("--- NODE: Research (Web Search) ---")
    query = state["query"]
    tavily_api_key = settings.TAVILY_API_KEY or os.environ.get("TAVILY_API_KEY")
    
    if not tavily_api_key:
        logger.warning("No TAVILY_API_KEY configured. Skipping web search.")
        return {
            "retrieved_contexts": [{
                "source": "web_mock",
                "doc_name": "Web Search Warning",
                "page": 1,
                "content": "Web search was requested but Tavily API key is not configured in the backend environment."
            }],
            "route": "generate"
        }
        
    try:
        logger.info(f"Querying Tavily Web Search: {query}")
        tavily = TavilyClient(api_key=tavily_api_key)
        response = tavily.search(query=query, max_results=5)
        
        formatted_contexts = []
        for result in response.get("results", []):
            formatted_contexts.append({
                "source": "web",
                "doc_name": result.get("title", "Web Result"),
                "url": result.get("url", ""),
                "content": result.get("content", "")
            })
            
        logger.info(f"Retrieved {len(formatted_contexts)} search results from Tavily.")
    except Exception as e:
        logger.error(f"Research node failed: {e}")
        formatted_contexts = []
        
    return {
        "retrieved_contexts": formatted_contexts,
        "route": "generate"
    }


def generate_node(state: AgentState) -> Dict[str, Any]:
    """
    Generates a draft response using the query and retrieved context.
    """
    logger.info("--- NODE: Generator ---")
    query = state["query"]
    contexts = state["retrieved_contexts"]
    
    # Format the retrieved contexts as text
    context_str = ""
    if contexts:
        context_str = "\n\n".join([
            f"Source [{ctx.get('source', 'unknown')}]: {ctx.get('doc_name', 'Web Result')} "
            f"(Page/URL: {ctx.get('page') or ctx.get('url') or 'N/A'})\nContent: {ctx['content']}"
            for ctx in contexts
        ])
    else:
        context_str = "No reference document context is currently available."
        
    system_prompt = """You are a highly analytical enterprise RAG assistant.
Your task is to write a comprehensive and helpful response to the User Query using ONLY the provided Reference Context.

Guidelines:
1. Ground your answer strictly in the provided Reference Context.
2. If the context does not contain enough information to fully answer the query, clearly state what information is missing.
3. Be professional, clear, and structured. Use Markdown tables, lists, or headers if they improve readability.
4. Do not make up facts or extrapolate beyond what is documented in the context.
"""

    prompt = f"""Reference Context:
{context_str}

User Query: "{query}"

Answer:"""

    llm = get_llm(temperature=0.2)
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        draft = response.content
        logger.info("Generated response draft successfully.")
    except Exception as e:
        logger.error(f"Generator node failed: {e}")
        draft = f"An error occurred while generating the answer: {e}"
        
    return {
        "draft_response": draft,
        "route": "verify"
    }


def verify_node(state: AgentState) -> Dict[str, Any]:
    """
    Audits the generated response against the context to verify faithfulness.
    If it detects hallucinations (score < 0.7) and attempts < 3, it triggers query expansion
    and redirects the agent back for another round of retrieval/research.
    """
    logger.info("--- NODE: Verifier (Guardrails) ---")
    contexts = state["retrieved_contexts"]
    draft = state["draft_response"]
    attempts = state.get("verification_attempts", 0) + 1
    
    if not contexts:
        # If there's no context, we can't perform faithfulness verification; pass it through.
        logger.info("No context available to verify against. Skipping validation.")
        return {
            "verification_score": 1.0,
            "verification_reasoning": "No retrieved context available for cross-referencing.",
            "route": "end",
            "verification_attempts": attempts
        }
        
    context_str = "\n\n".join([ctx["content"] for ctx in contexts])
    llm = get_llm(temperature=0.0)
    
    prompt = f"""You are an elite QA/hallucination verification assistant.
Your goal is to verify if the generated draft response is strictly faithful to the provided reference context.

Reference Context:
{context_str}

Generated Draft Response:
{draft}

Evaluate and return ONLY a JSON object containing:
- "score": A float from 0.0 to 1.0 representing faithfulness (1.0 = completely faithful, no hallucinations; 0.0 = completely fabricated or ungrounded).
- "reasoning": A detailed explanation of your score, pointing out any specific sentences that are unsupported or hallucinated.
- "missing_information": What specific topics, metrics, or details were missing in the context that would help answer the query fully? Write a revised, expanded search query that specifically aims to find these missing facts (or leave empty if score is high).

JSON Output:"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
            
        parsed = json.loads(content)
        score = float(parsed.get("score", 1.0))
        reasoning = parsed.get("reasoning", "")
        missing_query = parsed.get("missing_information", "")
        
        logger.info(f"Verification Score: {score} (Attempt {attempts}/3) | Reasoning: {reasoning}")
    except Exception as e:
        logger.error(f"Verifier node failed: {e}. Defaulting to passing score.")
        score = 1.0
        reasoning = "Verification failed to execute, defaulted to pass."
        missing_query = ""
        
    # Decision boundary
    if score < 0.70 and attempts < 3:
        # Determine routing back to retrieve or research based on context sources
        original_route = "retrieve"
        if contexts:
            if contexts[0].get("source") == "web":
                original_route = "research"
        # If there's a specific expanded query, use it to search again
        next_query = missing_query if missing_query else state["query"]
        logger.info(f"Hallucination detected! Routing back to '{original_route}' with query: {next_query}")
        return {
            "verification_score": score,
            "verification_reasoning": reasoning,
            "query": next_query,
            "verification_attempts": attempts,
            "route": original_route
        }
    else:
        logger.info("Verification passed or maximum attempts reached. Routing to end.")
        return {
            "verification_score": score,
            "verification_reasoning": reasoning,
            "verification_attempts": attempts,
            "route": "end"
        }

# --- Graph Assembly & Compile ---

def route_after_router(state: AgentState) -> str:
    return state["route"]

def route_after_verify(state: AgentState) -> str:
    return state["route"]

# Build state graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("research", research_node)
workflow.add_node("generate", generate_node)
workflow.add_node("verify", verify_node)

# Add edges
workflow.add_edge(START, "router")

# Router conditional routing
workflow.add_conditional_edges(
    "router",
    route_after_router,
    {
        "retrieve": "retrieve",
        "research": "research",
        "generate": "generate"
    }
)

# Connect retrievers to generator
workflow.add_edge("retrieve", "generate")
workflow.add_edge("research", "generate")

# Connect generator to verifier
workflow.add_edge("generate", "verify")

# Verifier conditional routing (loops back on failure, otherwise ends)
workflow.add_conditional_edges(
    "verify",
    route_after_verify,
    {
        "retrieve": "retrieve",
        "research": "research",
        "generate": "generate", # generate again with updated state
        "end": END
    }
)

# Compile graph
app_graph = workflow.compile()
