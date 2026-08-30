import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.models.state import AgentState
from app.models.schema import UserRole
from app.services.retrieval_service import RetrievalService

llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY, temperature=0)

# --- 1. SUPERVISOR AGENT ---
async def supervisor_node(state: AgentState) -> dict:
    """Interprets intent and routes to retrieval, research, or direct response."""
    user_query = state["messages"][-1]["content"]
    
    prompt = f"""
    You are the Supervisor Agent of a Commercial Bank AI Assistant.
    Analyze the user request and choose the best path:
    
    1. 'retrieval' - For general factual questions requiring knowledge lookup.
    2. 'research' - For complex, historical, multi-document batch summaries (e.g., outages over the last year, root cause aggregation).
    3. 'response' - If the query is conversational or can be answered directly without search.
    
    Respond strictly with JSON: {{"next_node": "retrieval" | "research" | "response"}}
    User Query: {user_query}
    """
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    try:
        decision = json.loads(response.content)
        next_node = decision.get("next_node", "retrieval")
    except Exception:
        next_node = "retrieval"
        
    return {"next_node": next_node}

# --- 2. RETRIEVAL AGENT ---
async def retrieval_node(state: AgentState) -> dict:
    """Performs single-pass hybrid RAG retrieval."""
    user_query = state["messages"][-1]["content"]
    user_role = state["user_role"]
    
    docs = await RetrievalService.hybrid_search(
        query=user_query,
        user_role=user_role,
        top_k=4
    )
    
    return {"retrieved_docs": docs, "next_node": "response"}

# --- 3. RESEARCH AGENT (RLM Pattern) ---
async def research_node(state: AgentState) -> dict:
    """Decomposes tasks into sub-plans, fetches batch evidence, and aggregates recursively."""
    user_query = state["messages"][-1]["content"]
    user_role = state["user_role"]
    
    # Task Decomposition: Break query into targeted sub-queries
    plan_prompt = f"""
    Decompose this complex research query into 2-3 specific sub-queries for vector retrieval.
    User Request: {user_query}
    Return JSON array of strings: ["query1", "query2"]
    """
    plan_res = await llm.ainvoke([HumanMessage(content=plan_prompt)])
    try:
        sub_queries = json.loads(plan_res.content)
    except Exception:
        sub_queries = [user_query]

    # Recursive Retrieval & Analysis across batches
    batch_results = []
    for q in sub_queries:
        docs = await RetrievalService.hybrid_search(query=q, user_role=user_role, top_k=3)
        
        # Intermediate mini-summary per sub-query
        summary_prompt = f"Summarize key facts from these documents for query '{q}':\n\n" + \
                         "\n".join([d['text'] for d in docs])
        batch_summary = await llm.ainvoke([HumanMessage(content=summary_prompt)])
        
        batch_results.append({
            "sub_query": q,
            "docs": docs,
            "summary": batch_summary.content
        })

    return {"research_batches": batch_results, "next_node": "response"}

# --- 4. RESPONSE AGENT ---
async def response_node(state: AgentState) -> dict:
    """Aggregates findings and generates final answer with citations."""
    messages = state["messages"]
    docs = state.get("retrieved_docs", [])
    batches = state.get("research_batches", [])
    
    context = ""
    if docs:
        context += "Retrieved Context:\n" + "\n".join([f"- [{d['document_id']}] {d['text']}" for d in docs])
    if batches:
        context += "\nResearch Aggregations:\n" + "\n".join([f"Sub-task ({b['sub_query']}): {b['summary']}" for b in batches])

    system_prompt = """
    You are an enterprise AI assistant for a Commercial Bank.
    Synthesize the response based ONLY on the provided context.
    Always attribute source document IDs where relevant.
    If context is insufficient, state it clearly.
    """
    
    formatted_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        formatted_messages.append(HumanMessage(content=msg["content"]) if msg["role"] == "user" else SystemMessage(content=msg["content"]))
    
    formatted_messages.append(HumanMessage(content=f"Context:\n{context}"))
    
    final_ans = await llm.ainvoke(formatted_messages)
    return {"final_response": final_ans.content, "next_node": "end"}