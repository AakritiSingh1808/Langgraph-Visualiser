# LangGraph Visualizer

Paste your [LangGraph](https://github.com/langchain-ai/langgraph) Python code and instantly get an **interactive diagram** of your agent workflow — plus automated insights about loops, dead ends, bottlenecks, complexity, and the state each node reads and writes.

No code execution. No setup in your project. Just paste and see your graph.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Cytoscape.js](https://img.shields.io/badge/Cytoscape.js-3.28-F7A70A)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Why this exists

LangGraph is great for building agentic workflows, but once a graph has conditional edges, retries, and multi-agent routing, it gets hard to reason about from the code alone. Questions like *"is there an infinite loop here?"*, *"which node is a traffic jam?"*, or *"what state does this node actually touch?"* require reading the whole file carefully.

This tool answers those questions automatically by **statically analyzing** your code (using Python's `ast` module — it never runs your code) and rendering it as an interactive graph.

## Features

- **Static AST parsing** — extracts nodes, edges, conditional edges, entry point, and `END` connections without executing anything
- **Interactive graph** — drag, zoom, pan, click-to-inspect, fullscreen — powered by Cytoscape.js + Dagre hierarchical layout
- **Automated insights**
  - Loop / cycle detection (infinite-loop risk) with the full cycle path
  - Dead-end detection (nodes that can't progress)
  - Bottleneck detection (nodes with 3+ incoming edges)
  - Complexity score (LOW / MEDIUM / HIGH)
- **State Inspector** — click any node to see which state keys it **reads** and **writes** (inferred from `state["key"]`, `state.get("key")`, and returned dicts)
- **5 built-in examples** — Simple Chain, RAG Agent, Builder-Executor, Multi-Agent (supervisor), Router
- **Export** — PNG, SVG, Mermaid code, or raw JSON
- **Shareable links** — graph is encoded into the URL
- **Robust parsing** — handles graphs inside functions/classes, `TypedDict` state, nodes added in loops, multiple graphs, and renamed `END` imports (`END as FINISH`)

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Parser | Python `ast` (static analysis, no execution) |
| Frontend | Single HTML file, vanilla JS, Cytoscape.js + Dagre (via CDN) |
| State | Stateless — no database |

## Architecture

```
Langraph_Visualiser/
├── backend/
│   ├── main.py          # FastAPI app: POST /parse, serves the frontend
│   ├── parser.py        # AST-based parser (nodes/edges/conditionals/state)
│   └── analyzer.py      # Loops, dead ends, bottlenecks, complexity
├── frontend/
│   └── index.html       # Single-file UI (Cytoscape.js)
├── examples/            # 5 example LangGraph scripts
├── requirements.txt
├── Procfile             # Railway / Heroku
├── render.yaml          # Render
└── README.md
```

The frontend talks to one endpoint (`POST /parse`). In production the same FastAPI server also serves `index.html`, so the whole thing deploys as a single web service.

## Quick start (local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server (serves both API and frontend)
uvicorn main:app --app-dir backend --reload

# 3. Open the app
#    http://localhost:8000
```

> You can also just open `frontend/index.html` directly as a file — it will
> automatically talk to a backend running on `http://localhost:8000`.

## Usage

1. Paste your LangGraph code in the left panel (or pick a built-in example).
2. Click **Visualize Graph**.
3. Explore: drag nodes, zoom/pan, go fullscreen, and **click a node** to open the inspector (connections, risk level, and state reads/writes).
4. Read the **Insights** panel for loops, dead ends, bottlenecks, and complexity.
5. **Export** or **Share** when you're happy.

## How it works

### 1. Parsing (`parser.py`)

The parser walks the AST and extracts:

- `StateGraph(...)` instantiation
- `add_node("name", handler)` — also maps the node to its handler function
- `add_edge("from", "to")`
- `add_conditional_edges("from", router, {...})`
- `set_entry_point("name")` and `END` references (including aliases)

For the **State Inspector**, it then opens each node's handler function and statically collects:
- **Reads** — `state["key"]`, `state['key']`, `state.get("key")`
- **Writes** — string keys in any returned dict (e.g. `return {"key": ...}`, including `{**state, "key": ...}`)

### 2. Output JSON

```json
{
  "nodes": ["retrieve", "grade", "generate", "rewrite", "END"],
  "edges": [{ "from": "retrieve", "to": "grade" }],
  "conditionals": [
    { "from": "grade", "router": "should_rewrite",
      "conditions": { "rewrite": "rewrite", "finish": "generate" } }
  ],
  "entry_point": "retrieve",
  "state_access": {
    "retrieve": { "reads": ["question"], "writes": ["documents"] }
  },
  "insights": {
    "has_loops": true,
    "dead_ends": [],
    "bottlenecks": [],
    "complexity_score": "MEDIUM"
  }
}
```

### 3. Analysis (`analyzer.py`)

- **Loops** — DFS with back-edge detection
- **Dead ends** — reachable nodes with no outgoing edges (and not `END`)
- **Bottlenecks** — in-degree ≥ 3 (counts the implicit `START → entry` edge)
- **Complexity** — `nodes×1 + edges×1.5 + conditionals×2`, bucketed into LOW / MEDIUM / HIGH

### 4. Rendering

The frontend converts the JSON into a Cytoscape graph with a Dagre top-to-bottom layout. Node shapes/colors encode meaning:

| Element | Style |
|---|---|
| START | green ellipse |
| END | red ellipse |
| Entry node | blue |
| Conditional source | orange diamond |
| Bottleneck | red octagon |
| Loop node | yellow, double border |
| Conditional edge | orange, labeled with the condition |
| Loop edge | dashed yellow |

## API

### `POST /parse`
**Body:** `{ "code": "<your LangGraph python>" }`
**Returns:** `nodes`, `edges`, `conditionals`, `entry_point`, `state_access`, `insights` (see JSON above).

### `GET /health`
Returns `{ "status": "healthy" }` (used for deploy health checks).

### `GET /`
Serves the frontend (or API info if the frontend file isn't present).

## Deployment

The app is a single web service (API + frontend). It honors the platform `PORT` env var.

**Render** — push to GitHub and point Render at the repo; `render.yaml` is included:
```
buildCommand:  pip install -r requirements.txt
startCommand:  uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

**Railway / Heroku** — the included `Procfile` handles it:
```
web: uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

> The runtime has **no heavy dependencies** — the parser uses only the standard
> library `ast` module, so builds are fast and reliable on free tiers.

## Examples

| Example | Pattern |
|---|---|
| `simple_chain.py` | Linear 4-node pipeline |
| `conditional_agent.py` | Intent classification with routing |
| `rag_agent.py` | Retrieve → grade → generate with a rewrite **loop** |
| `builder_executor.py` | Two-phase agent with retry + error handling |
| `multi_agent.py` | Supervisor routing to specialists (**bottleneck**) |
| `router.py` | Intent dispatch with low-confidence fallback |

## Limitations

- Static analysis only — dynamically constructed graphs may not fully resolve.
- State reads/writes are inferred from common patterns; unusual access (deep helpers, indirect mutation) may not be detected.
- Supports the common `StateGraph` API surface.

## License

MIT — free to use, modify, and share.
