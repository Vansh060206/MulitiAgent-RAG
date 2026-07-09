import operator
from typing import TypedDict, List, Dict, Any, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State definition for the Multi-Agent RAG workflow.
    Represents the shared memory passed between agent nodes in the graph.
    """
    
    # Conversation History
    # Annotated with 'add_messages' reducer. When a node outputs a message list,
    # LangGraph appends them to this list instead of overwriting the previous list.
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Target Search Query
    query: str
    
    # Collected Document/Context Passages
    # Annotated with 'operator.add'. When nodes return context passages,
    # they are concatenated into the list, accumulating knowledge.
    retrieved_contexts: Annotated[List[Dict[str, Any]], operator.add]
    
    # The current generated draft response text
    draft_response: str
    
    # State routing command (dictates which edge path to travel)
    # Valid targets: "retrieve", "research", "generate", "verify", "end"
    route: str
    
    # Verification and Hallucination scores
    verification_score: float  # Score from 0.0 to 1.0 (faithfulness)
    verification_reasoning: str # Explanations for the verification rating
    
    # Safety loop count to prevent infinite loop cycles if agent continues to fail
    verification_attempts: int
