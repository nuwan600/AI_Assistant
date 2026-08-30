from langgraph.graph import StateGraph, START, END
from app.models.state import AgentState
from app.services.agent_nodes import (
    supervisor_node,
    retrieval_node,
    research_node,
    response_node
)

# Initialize Graph
builder = StateGraph(AgentState)

# Add Agent Nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("retrieval", retrieval_node)
builder.add_node("research", research_node)
builder.add_node("response", response_node)

# Define Entry Point
builder.add_edge(START, "supervisor")

# Routing Function
def route_next(state: AgentState) -> str:
    return state["next_node"]

# Add Conditional Router from Supervisor
builder.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "retrieval": "retrieval",
        "research": "research",
        "response": "response"
    }
)

# Normal Edges to Response Node
builder.add_edge("retrieval", "response")
builder.add_edge("research", "response")

# Finish Flow
builder.add_conditional_edges(
    "response",
    lambda state: END
)

# Compile Compiled Graph
agent_app = builder.compile()