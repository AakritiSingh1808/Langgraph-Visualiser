"""
Simple Chain Example - Linear 4-node chain
Customer support ticket classification pipeline
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict


class TicketState(TypedDict):
    ticket_id: str
    message: str
    category: str
    priority: str
    assigned_to: str


def receive_ticket(state: TicketState) -> TicketState:
    """Receive and validate incoming ticket"""
    print(f"Received ticket {state['ticket_id']}: {state['message']}")
    return state


def classify_ticket(state: TicketState) -> TicketState:
    """Classify ticket by category"""
    message = state['message'].lower()
    if 'bug' in message or 'error' in message:
        category = 'bug'
    elif 'feature' in message or 'request' in message:
        category = 'feature_request'
    elif 'question' in message or 'how' in message:
        category = 'question'
    else:
        category = 'general'
    
    print(f"Classified as: {category}")
    return {**state, 'category': category}


def prioritize_ticket(state: TicketState) -> TicketState:
    """Assign priority level"""
    if state['category'] == 'bug':
        priority = 'high'
    elif state['category'] == 'feature_request':
        priority = 'medium'
    else:
        priority = 'low'
    
    print(f"Priority set to: {priority}")
    return {**state, 'priority': priority}


def assign_ticket(state: TicketState) -> TicketState:
    """Assign ticket to appropriate team"""
    assignment_map = {
        'bug': 'engineering_team',
        'feature_request': 'product_team',
        'question': 'support_team',
        'general': 'support_team'
    }
    assigned_to = assignment_map.get(state['category'], 'support_team')
    
    print(f"Assigned to: {assigned_to}")
    return {**state, 'assigned_to': assigned_to}


# Build the graph
graph = StateGraph(TicketState)

# Add nodes in sequence
graph.add_node("receive", receive_ticket)
graph.add_node("classify", classify_ticket)
graph.add_node("prioritize", prioritize_ticket)
graph.add_node("assign", assign_ticket)

# Linear flow: receive → classify → prioritize → assign → END
graph.set_entry_point("receive")
graph.add_edge("receive", "classify")
graph.add_edge("classify", "prioritize")
graph.add_edge("prioritize", "assign")
graph.add_edge("assign", END)

# Compile the graph
app = graph.compile()


# Test the graph
if __name__ == "__main__":
    result = app.invoke({
        "ticket_id": "TICK-1234",
        "message": "Found a critical bug in the login flow"
    })
    print(f"\nFinal ticket state: {result}")
