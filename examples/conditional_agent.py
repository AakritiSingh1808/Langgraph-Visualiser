"""
Conditional Agent Example - Routing based on state
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal


class AgentState(TypedDict):
    input: str
    classification: str
    response: str


def classify(state: AgentState) -> AgentState:
    """Classify the input"""
    input_text = state['input'].lower()
    
    if 'hello' in input_text or 'hi' in input_text:
        classification = 'greeting'
    elif 'help' in input_text or 'how' in input_text:
        classification = 'help'
    elif 'bye' in input_text or 'goodbye' in input_text:
        classification = 'farewell'
    else:
        classification = 'unknown'
    
    return {**state, 'classification': classification}


def handle_greeting(state: AgentState) -> AgentState:
    """Handle greeting messages"""
    return {**state, 'response': 'Hello! How can I help you today?'}


def handle_help(state: AgentState) -> AgentState:
    """Handle help requests"""
    return {**state, 'response': 'I can assist you with various tasks. What do you need?'}


def handle_farewell(state: AgentState) -> AgentState:
    """Handle farewell messages"""
    return {**state, 'response': 'Goodbye! Have a great day!'}


def handle_unknown(state: AgentState) -> AgentState:
    """Handle unknown messages"""
    return {**state, 'response': 'I\'m not sure how to respond to that.'}


def router(state: AgentState) -> Literal["greeting", "help", "farewell", "unknown", "end"]:
    """Route based on classification"""
    classification = state.get('classification', 'unknown')
    
    if classification == 'greeting':
        return "greeting"
    elif classification == 'help':
        return "help"
    elif classification == 'farewell':
        return "end"
    elif classification == 'unknown':
        return "unknown"
    
    return "end"


# Build the graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("classify", classify)
graph.add_node("greeting", handle_greeting)
graph.add_node("help", handle_help)
graph.add_node("farewell", handle_farewell)
graph.add_node("unknown", handle_unknown)

# Define the flow
graph.set_entry_point("classify")

# Add conditional routing
graph.add_conditional_edges(
    "classify",
    router,
    {
        "greeting": "greeting",
        "help": "help",
        "farewell": "farewell",
        "unknown": "unknown",
        "end": END
    }
)

# All response nodes go to END
graph.add_edge("greeting", END)
graph.add_edge("help", END)
graph.add_edge("farewell", END)
graph.add_edge("unknown", END)

# Compile the graph
app = graph.compile()


# Test the graph
if __name__ == "__main__":
    test_inputs = [
        "Hello there!",
        "Can you help me?",
        "Goodbye!",
        "What's the weather?"
    ]
    
    for input_text in test_inputs:
        print(f"\nInput: {input_text}")
        result = app.invoke({"input": input_text})
        print(f"Response: {result['response']}")
