import json
import asyncio
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.core.guardrails import GuardrailService
from app.models.state import AgentState
from app.services.retrieval_service import RetrievalService

logger = structlog.get_logger()
llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY, temperature=0, request_timeout=10)

# --- 1. SUPERVISOR AGENT WITH GUARDRAILS ---
async def supervisor_node(state: AgentState) -> dict:
    user_query = state["messages"][-1]["content"]
    
    # Run Guardrail Check
    try:
        GuardrailService.validate_user_input(user_query)
    except Exception as e:
        return {"final_response": str(e.detail if hasattr(e, 'detail') else e), "next_node": "end"}

    prompt = f"""
    You are the Supervisor Agent of Commercial Bank's AI Assistant.
    Analyze user request and choose:
    1. 'retrieval' - factual knowledge query
    2. 'research' - complex multi-document analysis
    3. 'response' - general conversation

    Respond with JSON: {{"next_node": "retrieval" | "research" | "response"}}
    User Query: {user_query}
    """
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        decision = json.loads(response.content)
        next_node = decision.get("next_node", "retrieval")
    except Exception as e:
        logger.warning("Supervisor routing failed, defaulting to retrieval", error=str(e))
        next_node = "retrieval"
        
    return {"next_node": next_node}

# --- 2. RETRIEVAL AGENT WITH DEGRADATION ---
async def retrieval_node(state: AgentState) -> dict:
    user_query = state["messages"][-1]["content"]
    user_role = state["user_role"]
    
    try:
        # Wrap search with a strict 5-second timeout
        docs = await asyncio.wait_for(
            RetrievalService.hybrid_search(query=user_query, user_role=user_role, top_k=4),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logger.error("Pinecone vector search timed out.")
        docs = []
    except Exception as e:
        logger.error("Retrieval failed", error=str(e))
        docs = []
        
    return {"retrieved_docs": docs, "next_node": "response"}

# --- 3. RESEARCH AGENT (RLM) WITH FALLBACK ---
async def research_node(state: AgentState) -> dict:
    user_query = state["messages"][-1]["content"]
    user_role = state["user_role"]
    
    try:
        plan_prompt = f"Decompose query into 2-3 sub-queries in JSON array format: {user_query}"
        plan_res = await llm.ainvoke([HumanMessage(content=plan_prompt)])
        sub_queries = json.loads(plan_res.content)
    except Exception:
        sub_queries = [user_query]

    batch_results = []
    for q in sub_queries:
        try:
            docs = await RetrievalService.hybrid_search(query=q, user_role=user_role, top_k=3)
            summary_prompt = f"Summarize facts for query '{q}':\n\n" + "\n".join([d['text'] for d in docs])
            batch_summary = await llm.ainvoke([HumanMessage(content=summary_prompt)])
            
            batch_results.append({
                "sub_query": q,
                "docs": docs,
                "summary": batch_summary.content
            })
        except Exception as e:
            logger.error("Error processing batch sub-query", sub_query=q, error=str(e))

    return {"research_batches": batch_results, "next_node": "response"}

# --- 4. RESPONSE AGENT WITH CITATION GUARDRAIL ---
async def response_node(state: AgentState) -> dict:
    messages = state["messages"]
    docs = state.get("retrieved_docs", [])
    batches = state.get("research_batches", [])
    
    # If initial guardrail triggered early termination
    if state.get("final_response"):
        return {"next_node": "end"}

    context = ""
    all_docs = list(docs)
    
    if docs:
        context += "Retrieved Context:\n" + "\n".join([f"- [{d['document_id']}] {d['text']}" for d in docs])
    if batches:
        context += "\nResearch Aggregations:\n"
        for b in batches:
            context += f"Sub-task ({b['sub_query']}): {b['summary']}\n"
            all_docs.extend(b.get("docs", []))

    system_prompt = """
    You are the official conversational assistant for Commercial Bank.
    Maintain professional brand voice.
    Synthesize answers based strictly on provided context.
    Cite sources using document IDs (e.g. [doc_001]).
    If context is insufficient, state: 'I do not have enough internal information to answer this query.'
    """
    
    formatted_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        formatted_messages.append(HumanMessage(content=msg["content"]) if msg["role"] == "user" else SystemMessage(content=msg["content"]))
    
    formatted_messages.append(HumanMessage(content=f"Context:\n{context}"))
    
    try:
        final_ans = await llm.ainvoke(formatted_messages)
        content = final_ans.content
    except Exception as e:
        logger.error("LLM Generation failed", error=str(e))
        content = "We are currently experiencing service disruptions. Unable to complete your request."

    # Output Guardrail: Validate citations
    validated_content = GuardrailService.validate_output_citations(content, all_docs)
    
    return {"final_response": validated_content, "next_node": "end"}