"""
Router Example - An intent classifier dispatches a query to a specialized
handler. Demonstrates a fan-out conditional with a low-confidence fallback.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict


class QueryState(TypedDict):
    query: str
    intent: str
    confidence: float
    response: str


def classify_intent(state):
    query = state["query"]
    return {"intent": "billing", "confidence": 0.92}


def handle_billing(state):
    return {"response": "Billing handled for: " + state["query"]}


def handle_technical(state):
    return {"response": "Technical support for: " + state["query"]}


def handle_general(state):
    return {"response": "General answer for: " + state["query"]}


def fallback(state):
    return {"response": "Escalating to a human agent."}


def route_intent(state):
    if state["confidence"] < 0.5:
        return "fallback"
    return state["intent"]


graph = StateGraph(QueryState)
graph.add_node("classify", classify_intent)
graph.add_node("billing", handle_billing)
graph.add_node("technical", handle_technical)
graph.add_node("general", handle_general)
graph.add_node("fallback", fallback)

graph.set_entry_point("classify")

graph.add_conditional_edges(
    "classify",
    route_intent,
    {
        "billing": "billing",
        "technical": "technical",
        "general": "general",
        "fallback": "fallback",
    },
)

graph.add_edge("billing", END)
graph.add_edge("technical", END)
graph.add_edge("general", END)
graph.add_edge("fallback", END)

app = graph.compile()
