"""
Graph Analysis Module
Detects loops, dead ends, bottlenecks, and calculates complexity score
"""

from typing import Dict, List, Set, Any
from collections import defaultdict, deque


class GraphAnalyzer:
    """Analyze LangGraph structure for insights"""
    
    def __init__(self, graph_data: Dict[str, Any]):
        self.nodes = graph_data.get("nodes", [])
        self.edges = graph_data.get("edges", [])
        self.conditionals = graph_data.get("conditionals", [])
        self.entry_point = graph_data.get("entry_point")
        
        # Build adjacency list
        self.adjacency = self._build_adjacency_list()
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete graph analysis
        
        Returns:
            Dictionary with insights about the graph
        """
        return {
            "has_loops": self.detect_loops(),
            "dead_ends": self.find_dead_ends(),
            "bottlenecks": self.find_bottlenecks(),
            "complexity_score": self.calculate_complexity()
        }
    
    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """Build adjacency list representation of the graph"""
        adj = defaultdict(list)
        
        # Add regular edges
        for edge in self.edges:
            adj[edge["from"]].append(edge["to"])
        
        # Add conditional edges
        for cond in self.conditionals:
            for dest in cond["conditions"].values():
                adj[cond["from"]].append(dest)
        
        return dict(adj)
    
    def detect_loops(self) -> bool:
        """
        Detect if the graph contains any cycles/loops
        Uses DFS with color marking (white, gray, black)
        """
        if not self.nodes or not self.entry_point:
            return False
        
        # Color: white (0) = unvisited, gray (1) = in progress, black (2) = done
        color = {node: 0 for node in self.nodes}
        
        def dfs(node: str) -> bool:
            """DFS to detect back edges (cycles)"""
            if node not in color:
                return False
            
            if color[node] == 1:  # Gray - back edge found (cycle)
                return True
            
            if color[node] == 2:  # Black - already processed
                return False
            
            color[node] = 1  # Mark as gray (in progress)
            
            # Visit all neighbors
            for neighbor in self.adjacency.get(node, []):
                if neighbor == "END":  # Skip END node
                    continue
                if dfs(neighbor):
                    return True
            
            color[node] = 2  # Mark as black (done)
            return False
        
        # Start DFS from entry point
        if self.entry_point:
            return dfs(self.entry_point)
        
        return False
    
    def find_dead_ends(self) -> List[str]:
        """
        Find dead end nodes:
        - Nodes with no outgoing edges that aren't END
        - Nodes that cannot reach END
        """
        if "END" not in self.nodes:
            return []
        
        dead_ends = []
        
        # Find nodes with no outgoing edges (and aren't END)
        for node in self.nodes:
            if node != "END":
                outgoing = self.adjacency.get(node, [])
                if len(outgoing) == 0:
                    # This node has no outgoing edges - it's a dead end
                    if self._is_reachable_from_entry(node):
                        dead_ends.append(node)
        
        return dead_ends
    
    def _is_reachable_from_entry(self, target: str) -> bool:
        """Check if target node is reachable from entry point"""
        if not self.entry_point:
            return False
        
        visited = set()
        queue = deque([self.entry_point])
        
        while queue:
            node = queue.popleft()
            if node == target:
                return True
            
            if node in visited:
                continue
            
            visited.add(node)
            
            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return False
    
    def find_bottlenecks(self) -> List[str]:
        """
        Find bottleneck nodes:
        - Nodes with 3+ incoming edges (many nodes converge here)
        - Includes edge from START to entry point
        """
        in_degree = defaultdict(int)
        
        # Count edge from START to entry point
        if self.entry_point and self.entry_point != "END":
            in_degree[self.entry_point] += 1
        
        # Count in-degree for each node from regular edges and conditionals
        for from_node, neighbors in self.adjacency.items():
            for to_node in neighbors:
                in_degree[to_node] += 1
        
        bottlenecks = []
        threshold = 3  # Nodes with 3+ incoming edges
        
        for node in self.nodes:
            if node != "END":
                if in_degree[node] >= threshold:
                    bottlenecks.append(node)
        
        return bottlenecks
    
    def calculate_complexity(self) -> str:
        """
        Calculate graph complexity and return as LOW / MEDIUM / HIGH
        
        Formula: (num_nodes * 1) + (num_edges * 1.5) + (num_conditionals * 2)
        
        Ranges:
        - LOW: score < 10
        - MEDIUM: 10 <= score < 20
        - HIGH: score >= 20
        """
        # Calculate base score
        score = 0
        score += len(self.nodes) * 1
        score += len(self.edges) * 1.5
        score += len(self.conditionals) * 2
        
        # Categorize
        if score < 10:
            return "LOW"
        elif score < 20:
            return "MEDIUM"
        else:
            return "HIGH"


def analyze_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze a parsed graph
    
    Args:
        graph_data: Parsed graph data from parser
        
    Returns:
        Dictionary with analysis insights
    """
    analyzer = GraphAnalyzer(graph_data)
    return analyzer.analyze()
