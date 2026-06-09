"""
RAG Agent Example - Retrieval Augmented Generation
Pattern: retrieve → grade → generate → conditional rewrite loop
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List


class RAGState(TypedDict):
    question: str
    documents: List[str]
    relevance_score: float
    answer: str
    attempts: int


def retrieve_documents(state: RAGState) -> RAGState:
    """Retrieve relevant documents from knowledge base"""
    question = state['question']
    
    # Simulate document retrieval
    mock_docs = [
        f"Document about {question}",
        "General information document",
        f"Technical details on {question}"
    ]
    
    print(f"Retrieved {len(mock_docs)} documents for: {question}")
    return {**state, 'documents': mock_docs, 'attempts': state.get('attempts', 0) + 1}


def grade_documents(state: RAGState) -> RAGState:
    """Grade document relevance to the question"""
    # Simulate relevance scoring
    relevance_score = 0.75 if state['attempts'] == 1 else 0.85
    
    print(f"Document relevance score: {relevance_score}")
    return {**state, 'relevance_score': relevance_score}


def generate_answer(state: RAGState) -> RAGState:
    """Generate answer using relevant documents"""
    answer = f"Based on {len(state['documents'])} documents: Answer to '{state['question']}'"
    
    print(f"Generated answer: {answer}")
    return {**state, 'answer': answer}


def rewrite_question(state: RAGState) -> RAGState:
    """Rewrite question for better retrieval"""
    original = state['question']
    rewritten = f"{original} (refined query)"
    
    print(f"Rewriting question: {original} -> {rewritten}")
    return {**state, 'question': rewritten}


def should_rewrite(state: RAGState) -> str:
    """Decide whether to rewrite the question or finish"""
    # If relevance is low and we haven't tried too many times
    if state['relevance_score'] < 0.8 and state['attempts'] < 2:
        return "rewrite"
    else:
        return "finish"


# Build the graph
graph = StateGraph(RAGState)

# Add nodes
graph.add_node("retrieve", retrieve_documents)
graph.add_node("grade", grade_documents)
graph.add_node("generate", generate_answer)
graph.add_node("rewrite", rewrite_question)

# Set entry point
graph.set_entry_point("retrieve")

# Linear flow for main path
graph.add_edge("retrieve", "grade")
graph.add_edge("generate", END)

# Conditional routing after grading
graph.add_conditional_edges(
    "grade",
    should_rewrite,
    {
        "rewrite": "rewrite",  # Low relevance: rewrite and retry
        "finish": "generate"   # Good relevance: proceed to generate
    }
)

# Loop: rewrite goes back to retrieve
graph.add_edge("rewrite", "retrieve")

# Compile the graph
app = graph.compile()


# Test the graph
if __name__ == "__main__":
    result = app.invoke({
        "question": "How does RAG work?",
        "attempts": 0
    })
    print(f"\nFinal answer: {result['answer']}")
    print(f"Total attempts: {result['attempts']}")
