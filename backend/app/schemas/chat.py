from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    """Schema representing a client search query request."""
    query: str = Field(..., min_length=1, description="The search query text.")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks to retrieve.")

class ChatTraceItem(BaseModel):
    node: str = Field(..., description="The name of the agent node executed.")
    details: str = Field(..., description="The actions or details from this step.")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The final verified response from the multi-agent system.")
    trace: List[ChatTraceItem] = Field(default=[], description="The step-by-step trace of agent execution.")
    sources: List[Dict[str, Any]] = Field(default=[], description="The context documents used to ground the answer.")
    verification_score: float = Field(..., description="The final hallucination/faithfulness score.")
    verification_reasoning: str = Field(..., description="The reasoning behind the verification score.")
