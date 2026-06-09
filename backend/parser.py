"""
LangGraph Code Parser using Python AST
Extracts nodes, edges, conditional edges, entry points, and END connections
"""

import ast
from typing import Dict, List, Any, Optional


class LangGraphParser:
    """Parse LangGraph StateGraph definitions from Python code"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.conditional_edges = []
        self.entry_point = None
        self.graph_variables = []  # Track multiple graphs
        self.end_aliases = ["END"]  # Track different names for END
        self.node_functions = {}  # Map node name -> handler function name
        self.function_defs = {}  # Map function name -> ast.FunctionDef node
        self.state_access = {}  # Map node name -> {"reads": [...], "writes": [...]}
        
    def parse(self, code: str) -> Dict[str, Any]:
        """
        Parse LangGraph Python code and extract graph structure
        
        Args:
            code: Python code containing LangGraph StateGraph definition
            
        Returns:
            Dictionary with nodes, edges, conditionals, and entry_point
        """
        try:
            tree = ast.parse(code)
            self._extract_graph_info(tree)
            
            # Add END node if referenced
            if self._has_end_reference():
                if "END" not in self.nodes:
                    self.nodes.append("END")
            
            # Inspect each node's handler function for state reads/writes
            self._extract_state_access()
            
            return {
                "nodes": self.nodes,
                "edges": self.edges,
                "conditionals": self.conditional_edges,
                "entry_point": self.entry_point,
                "state_access": self.state_access
            }
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse code: {str(e)}")
    
    def _extract_graph_info(self, tree: ast.AST):
        """Walk through AST and extract graph components"""
        # First pass: find import aliases for END
        self._extract_end_aliases(tree)
        
        # Second pass: extract graph information
        for node in ast.walk(tree):
            # Collect function definitions for later state inspection
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.function_defs[node.name] = node
            
            # Find StateGraph instantiation
            if isinstance(node, ast.Assign):
                if self._is_stategraph_assignment(node):
                    var_name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else None
                    if var_name and var_name not in self.graph_variables:
                        self.graph_variables.append(var_name)
            
            # Find method calls on the graph
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    self._process_graph_method(node)
    
    def _is_stategraph_assignment(self, node: ast.Assign) -> bool:
        """Check if this is a StateGraph() assignment"""
        if not isinstance(node.value, ast.Call):
            return False
        
        func = node.value.func
        if isinstance(func, ast.Name) and func.id == "StateGraph":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "StateGraph":
            return True
        
        return False
    
    def _process_graph_method(self, node: ast.Call):
        """Process method calls on the graph object"""
        method_name = node.func.attr
        
        if method_name == "add_node":
            self._process_add_node(node)
        elif method_name == "add_edge":
            self._process_add_edge(node)
        elif method_name == "add_conditional_edges":
            self._process_add_conditional_edges(node)
        elif method_name == "set_entry_point":
            self._process_set_entry_point(node)
    
    def _process_add_node(self, node: ast.Call):
        """Extract node name (and its handler function) from add_node call"""
        if len(node.args) >= 1:
            node_name = self._extract_string_value(node.args[0])
            if node_name and node_name not in self.nodes:
                self.nodes.append(node_name)
            # Capture the handler function name (second positional arg)
            if node_name and len(node.args) >= 2:
                func_name = self._extract_function_name(node.args[1])
                if func_name:
                    self.node_functions[node_name] = func_name
    
    def _process_add_edge(self, node: ast.Call):
        """Extract edge from add_edge call"""
        if len(node.args) >= 2:
            from_node = self._extract_string_or_constant(node.args[0])
            to_node = self._extract_string_or_constant(node.args[1])
            
            if from_node and to_node:
                # Normalize END references
                from_node = self._normalize_end_reference(from_node)
                to_node = self._normalize_end_reference(to_node)
                self.edges.append({"from": from_node, "to": to_node})
    
    def _process_add_conditional_edges(self, node: ast.Call):
        """Extract conditional edges from add_conditional_edges call"""
        if len(node.args) >= 3:
            from_node = self._extract_string_value(node.args[0])
            # Second arg is the router function (we just need the name)
            router_func = self._extract_function_name(node.args[1])
            # Third arg is the mapping dict
            conditions = self._extract_dict_mapping(node.args[2])
            
            if from_node and conditions:
                # Normalize END references in conditions
                normalized_conditions = {}
                for key, value in conditions.items():
                    normalized_conditions[key] = self._normalize_end_reference(value)
                
                self.conditional_edges.append({
                    "from": from_node,
                    "router": router_func,
                    "conditions": normalized_conditions
                })
    
    def _process_set_entry_point(self, node: ast.Call):
        """Extract entry point from set_entry_point call"""
        if len(node.args) >= 1:
            self.entry_point = self._extract_string_value(node.args[0])
    
    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """Extract string value from AST node"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            return node.s
        return None
    
    def _extract_string_or_constant(self, node: ast.AST) -> Optional[str]:
        """Extract string value or constant name (like END)"""
        # Check if it's a string literal
        string_val = self._extract_string_value(node)
        if string_val:
            return string_val
        
        # Check if it's a Name reference (like END)
        if isinstance(node, ast.Name):
            return node.id
        
        # Check if it's an attribute (like graph.END)
        if isinstance(node, ast.Attribute):
            return node.attr
        
        return None
    
    def _extract_function_name(self, node: ast.AST) -> Optional[str]:
        """Extract function name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
    
    def _extract_dict_mapping(self, node: ast.AST) -> Dict[str, str]:
        """Extract dictionary mapping from AST node"""
        if not isinstance(node, ast.Dict):
            return {}
        
        mapping = {}
        for key, value in zip(node.keys, node.values):
            key_str = self._extract_string_value(key)
            value_str = self._extract_string_or_constant(value)
            if key_str and value_str:
                mapping[key_str] = value_str
        
        return mapping
    
    def _extract_end_aliases(self, tree: ast.AST):
        """Find all aliases for END (e.g., 'from langgraph.graph import END as FINISH')"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'langgraph' in node.module:
                    for alias in node.names:
                        if alias.name == "END":
                            if alias.asname:
                                self.end_aliases.append(alias.asname)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if 'langgraph' in alias.name:
                        if alias.asname:
                            self.end_aliases.append(f"{alias.asname}.END")
    
    def _is_end_reference(self, value: str) -> bool:
        """Check if a value is a reference to END (including aliases)"""
        if not value:
            return False
        return value in self.end_aliases or value.endswith(".END")
    
    def _normalize_end_reference(self, value: str) -> str:
        """Normalize END references to 'END'"""
        if self._is_end_reference(value):
            return "END"
        return value
    
    def _has_end_reference(self) -> bool:
        """Check if END is referenced in edges or conditionals"""
        # Check regular edges
        for edge in self.edges:
            if self._is_end_reference(edge["to"]):
                return True
        
        # Check conditional edges
        for cond in self.conditional_edges:
            for dest in cond["conditions"].values():
                if self._is_end_reference(dest):
                    return True
        
        return False
    
    def _extract_state_access(self):
        """
        For each node, inspect its handler function (if available) and
        statically determine which state keys it reads and writes.

        Reads  -> state["key"], state['key'], state.get("key")
        Writes -> string keys in any returned dict, e.g. return {"key": ...}
        """
        for node_name in self.nodes:
            if node_name == "END":
                continue
            
            func_name = self.node_functions.get(node_name)
            func_def = self.function_defs.get(func_name) if func_name else None
            
            if not func_def:
                # No handler we can inspect (e.g. lambda or external function)
                self.state_access[node_name] = {"reads": [], "writes": []}
                continue
            
            state_param = self._get_state_param_name(func_def)
            reads = self._extract_state_reads(func_def, state_param)
            writes = self._extract_state_writes(func_def)
            
            self.state_access[node_name] = {
                "reads": sorted(reads),
                "writes": sorted(writes)
            }
    
    def _get_state_param_name(self, func_def: ast.AST) -> Optional[str]:
        """Get the name of the first parameter (the state argument)"""
        args = func_def.args.args
        if args:
            return args[0].arg
        return None
    
    def _extract_state_reads(self, func_def: ast.AST, state_param: Optional[str]) -> set:
        """Find state keys that are read inside the function body"""
        reads = set()
        if not state_param:
            return reads
        
        for node in ast.walk(func_def):
            # state["key"] or state['key']
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == state_param:
                    key = self._extract_subscript_key(node)
                    if key:
                        reads.add(key)
            
            # state.get("key")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (node.func.attr == "get"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == state_param
                        and node.args):
                    key = self._extract_string_value(node.args[0])
                    if key:
                        reads.add(key)
        
        return reads
    
    def _extract_state_writes(self, func_def: ast.AST) -> set:
        """Find state keys written via returned dict literals"""
        writes = set()
        
        for node in ast.walk(func_def):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    # key is None for dict unpacking like {**state, ...}
                    if key is not None:
                        key_str = self._extract_string_value(key)
                        if key_str:
                            writes.add(key_str)
        
        return writes
    
    def _extract_subscript_key(self, node: ast.Subscript) -> Optional[str]:
        """Extract the string key from a subscript node (handles py<3.9 Index)"""
        sl = node.slice
        # Python 3.9+: slice is the expression directly
        key = self._extract_string_value(sl)
        if key:
            return key
        # Python <3.9: slice wrapped in ast.Index
        if isinstance(sl, ast.Index):
            return self._extract_string_value(sl.value)
        return None


def parse_langgraph_code(code: str) -> Dict[str, Any]:
    """
    Convenience function to parse LangGraph code
    
    Args:
        code: Python code containing LangGraph StateGraph definition
        
    Returns:
        Dictionary with nodes, edges, conditionals, and entry_point
    """
    parser = LangGraphParser()
    return parser.parse(code)
