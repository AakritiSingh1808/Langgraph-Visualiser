"""
Multi-Agent Example - A supervisor routes work to specialist agents.

All specialist agents report back to the supervisor, which makes the
supervisor a bottleneck node (3+ incoming edges) - a useful pattern to
visualize and analyze.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List


class TeamState(TypedDict):
    task: str
    next_agent: str
    research_notes: str
    code: str
    review: str
    messages: List[str]


def supervisor(state):
    """Decide which specialist should act next."""
    task = state["task"]
    return {"next_agent": "researcher", "messages": state["messages"] + ["routing"]}


def researcher(state):
    notes = "findings for: " + state["task"]
    return {"research_notes": notes}


def coder(state):
    return {"code": "def solution(): pass"}


def reviewer(state):
    return {"review": "looks good", "next_agent": "done"}


def route_next(state):
    return state["next_agent"]


graph = StateGraph(TeamState)
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", researcher)
graph.add_node("coder", coder)
graph.add_node("reviewer", reviewer)

graph.set_entry_point("supervisor")

# All agents report back to supervisor (makes supervisor a bottleneck)
graph.add_edge("researcher", "supervisor")
graph.add_edge("coder", "supervisor")
graph.add_edge("reviewer", "supervisor")

graph.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "researcher": "researcher",
        "coder": "coder",
        "reviewer": "reviewer",
        "done": END,
    },
)

app = graph.compile()
