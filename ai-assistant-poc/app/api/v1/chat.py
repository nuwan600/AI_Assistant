from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from app.api.deps import get_current_user
from app.models.schema import User
from app.services.agent_workflow import agent_app

router = APIRouter()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

@router.post("/completions")
async def chat_completion(request: ChatRequest, current_user: User = Depends(get_current_user)):
    initial_state = {
        "messages": request.messages,
        "user_role": current_user.role,
        "next_node": "supervisor",
        "search_queries": [],
        "retrieved_docs": [],
        "research_batches": [],
        "final_response": None,
        "error": None
    }
    
    # Execute LangGraph Workflow
    final_output = await agent_app.ainvoke(initial_state)
    
    return {
        "response": final_output.get("final_response"),
        "user_role": current_user.role,
        "execution_summary": {
            "retrieved_count": len(final_output.get("retrieved_docs", [])),
            "research_batches_count": len(final_output.get("research_batches", []))
        }
    }