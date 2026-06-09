"""
FastAPI Backend for LangGraph Visualizer
Provides /parse endpoint to parse LangGraph code and return graph structure
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

from parser import parse_langgraph_code
from analyzer import analyze_graph

# Path to the single-file frontend (../frontend/index.html)
FRONTEND_FILE = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


app = FastAPI(
    title="LangGraph Visualizer API",
    description="Parse and analyze LangGraph StateGraph definitions",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeInput(BaseModel):
    """Request model for code parsing"""
    code: str


class ParseResponse(BaseModel):
    """Response model for parsed graph"""
    nodes: list
    edges: list
    conditionals: list
    entry_point: str | None
    state_access: Dict[str, Any] = {}
    insights: Dict[str, Any]


@app.get("/")
async def root():
    """Serve the frontend if available, otherwise return API info"""
    if FRONTEND_FILE.exists():
        return FileResponse(str(FRONTEND_FILE))
    return {
        "status": "ok",
        "service": "LangGraph Visualizer API",
        "version": "1.0.0"
    }


@app.post("/parse", response_model=ParseResponse)
async def parse_code(input_data: CodeInput):
    """
    Parse LangGraph code and return graph structure with insights
    
    Args:
        input_data: CodeInput with Python code containing LangGraph StateGraph
        
    Returns:
        ParseResponse with nodes, edges, conditionals, entry_point, and insights
        
    Raises:
        HTTPException: If code parsing fails
    """
    try:
        # Parse the code
        graph_data = parse_langgraph_code(input_data.code)
        
        # Analyze the graph
        insights = analyze_graph(graph_data)
        
        # Combine results
        response = {
            **graph_data,
            "insights": insights
        }
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # Honor the platform-provided PORT (Render/Railway/Heroku), default to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
