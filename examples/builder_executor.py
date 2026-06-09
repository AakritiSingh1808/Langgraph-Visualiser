"""
Builder-Executor Pattern Example
Two-phase agent: builder node generates a plan, executor node runs it
Conditional routing based on success/failure
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict


class TaskState(TypedDict):
    user_request: str
    plan: List[Dict[str, str]]
    current_step: int
    execution_log: List[str]
    success: bool
    error_message: str


def builder(state: TaskState) -> TaskState:
    """Builder phase: Generate execution plan"""
    request = state['user_request']
    
    # Generate a plan based on the request
    plan = [
        {"action": "validate_input", "description": f"Validate: {request}"},
        {"action": "fetch_data", "description": "Fetch required data from database"},
        {"action": "process_data", "description": "Process and transform data"},
        {"action": "generate_output", "description": "Generate final output"}
    ]
    
    print(f"Builder: Created plan with {len(plan)} steps")
    for i, step in enumerate(plan):
        print(f"  Step {i+1}: {step['description']}")
    
    return {
        **state,
        'plan': plan,
        'current_step': 0,
        'execution_log': [],
        'success': False
    }


def executor(state: TaskState) -> TaskState:
    """Executor phase: Run the current step of the plan"""
    plan = state['plan']
    current_step = state['current_step']
    execution_log = state['execution_log'].copy()
    
    if current_step < len(plan):
        step = plan[current_step]
        print(f"Executor: Running step {current_step + 1}: {step['action']}")
        
        # Simulate execution (90% success rate)
        import random
        success = random.random() > 0.1
        
        if success:
            log_entry = f"✓ Step {current_step + 1} completed: {step['action']}"
            execution_log.append(log_entry)
            return {
                **state,
                'current_step': current_step + 1,
                'execution_log': execution_log,
                'error_message': ''
            }
        else:
            error_msg = f"Failed at step {current_step + 1}: {step['action']}"
            return {
                **state,
                'error_message': error_msg,
                'success': False
            }
    
    # All steps completed
    return {**state, 'success': True}


def validator(state: TaskState) -> TaskState:
    """Validate that all steps completed successfully"""
    if state['current_step'] >= len(state['plan']):
        print("Validator: All steps completed successfully")
        return {**state, 'success': True}
    
    return state


def error_handler(state: TaskState) -> TaskState:
    """Handle execution errors and log them"""
    print(f"Error Handler: {state['error_message']}")
    execution_log = state['execution_log'].copy()
    execution_log.append(f"✗ Error: {state['error_message']}")
    
    return {**state, 'execution_log': execution_log}


def route_executor(state: TaskState) -> str:
    """Route based on executor result"""
    if state.get('error_message'):
        return "error"
    elif state['current_step'] >= len(state['plan']):
        return "validate"
    else:
        return "continue"


def route_validator(state: TaskState) -> str:
    """Route based on validation result"""
    if state['success']:
        return "finish"
    else:
        return "error"


# Build the graph
graph = StateGraph(TaskState)

# Add nodes
graph.add_node("builder", builder)
graph.add_node("executor", executor)
graph.add_node("validator", validator)
graph.add_node("error_handler", error_handler)

# Set entry point
graph.set_entry_point("builder")

# Builder always goes to executor
graph.add_edge("builder", "executor")

# Executor has conditional routing
graph.add_conditional_edges(
    "executor",
    route_executor,
    {
        "continue": "executor",    # Loop: next step
        "validate": "validator",   # All steps done: validate
        "error": "error_handler"   # Error: handle it
    }
)

# Validator has conditional routing
graph.add_conditional_edges(
    "validator",
    route_validator,
    {
        "finish": END,            # Success: finish
        "error": "error_handler"  # Failure: handle error
    }
)

# Error handler goes to END (could retry instead)
graph.add_edge("error_handler", END)

# Compile the graph
app = graph.compile()


# Test the graph
if __name__ == "__main__":
    result = app.invoke({
        "user_request": "Generate monthly sales report"
    })
    
    print(f"\n{'='*50}")
    print(f"Final Status: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Steps Completed: {result['current_step']}/{len(result['plan'])}")
    print(f"\nExecution Log:")
    for log_entry in result['execution_log']:
        print(f"  {log_entry}")
