from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from langsmith import traceable
from app.api.deps import get_current_user
from app.models.schema import User
from app.services.agent_workflow import agent_app

router = APIRouter()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

@router.post("/completions")
@traceable(name="chat_completion_endpoint", run_type="chain")
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
    
    # Execute LangGraph Workflow with tracing config
    trace_config = {
        "run_name": "Enterprise_AI_Assistant_Workflow",
        "tags": ["chat_workflow", f"role:{current_user.role}", f"user:{current_user.username}"],
        "metadata": {
            "username": current_user.username,
            "user_role": str(current_user.role),
            "message_count": len(request.messages)
        }
    }
    
    final_output = await agent_app.ainvoke(initial_state, config=trace_config)
    
    return {
        "response": final_output.get("final_response"),
        "user_role": current_user.role,
        "execution_summary": {
            "retrieved_count": len(final_output.get("retrieved_docs", [])),
            "research_batches_count": len(final_output.get("research_batches", []))
        }
    }