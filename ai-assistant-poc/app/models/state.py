from typing import TypedDict, List, Dict, Any, Optional
from app.models.schema import UserRole

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    user_role: UserRole
    next_node: str
    search_queries: List[str]
    retrieved_docs: List[Dict[str, Any]]
    research_batches: List[Dict[str, Any]]
    final_response: Optional[str]
    error: Optional[str]