"""
Directed Acyclic Graph (DAG) implementation for fractal-down.

Provides immutable DAG nodes and a DAG class for building and querying
computational graphs with cycle detection and topological ordering.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, NamedTuple
from collections import defaultdict, deque


class Node(NamedTuple):
    """Immutable DAG node."""
    id: int
    name: str
    op: Optional[Callable[..., Any]]  # None => leaf
    inputs: Tuple[int, ...]           # parent IDs
    meta: Tuple[Tuple[str, Any], ...]  # sorted (k,v), strings via str()


class DAG:
    """
    Directed Acyclic Graph for computational operations.
    
    Maintains nodes with dependencies and provides topology-aware operations
    with cycle detection and deterministic ordering.
    """
    
    def __init__(self):
        self._nodes: Dict[int, Node] = {}
        self._children: Dict[int, List[int]] = defaultdict(list)
        self._next_id = 0
        self._postorder_cache: Dict[int, List[int]] = {}
    
    def add_leaf(self, name: str, meta: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a leaf node (no operation, input data).
        
        Args:
            name: Human-readable name for the node
            meta: Optional metadata dictionary
            
        Returns:
            The ID of the created node
        """
        node_id = self._next_id
        self._next_id += 1
        
        # Convert meta to sorted tuple of string key-value pairs
        sorted_meta = self._serialize_meta(meta or {})
        
        node = Node(
            id=node_id,
            name=name,
            op=None,
            inputs=(),
            meta=sorted_meta
        )
        
        self._nodes[node_id] = node
        self._postorder_cache.clear()
        return node_id
    
    def add_op(self, name: str, op: Callable[..., Any], inputs: Iterable[int], 
               meta: Optional[Dict[str, Any]] = None) -> int:
        """
        Add an operation node.
        
        Args:
            name: Human-readable name for the node
            op: Callable operation to perform
            inputs: Iterable of parent node IDs
            meta: Optional metadata dictionary
            
        Returns:
            The ID of the created node
            
        Raises:
            ValueError: If input nodes don't exist or would create a cycle
        """
        node_id = self._next_id
        self._next_id += 1
        
        input_ids = tuple(inputs)
        
        # Validate that all input nodes exist
        for input_id in input_ids:
            if input_id not in self._nodes:
                raise ValueError(f"Input node {input_id} does not exist")
        
        # Convert meta to sorted tuple of string key-value pairs  
        sorted_meta = self._serialize_meta(meta or {})
        
        node = Node(
            id=node_id,
            name=name,
            op=op,
            inputs=input_ids,
            meta=sorted_meta
        )
        
        # Check for cycles before adding
        self._nodes[node_id] = node
        for input_id in input_ids:
            self._children[input_id].append(node_id)
        
        if self._has_cycle(node_id):
            # Rollback the addition
            del self._nodes[node_id]
            for input_id in input_ids:
                self._children[input_id].remove(node_id)
            raise ValueError(f"Adding node {node_id} would create a cycle")
        
        self._postorder_cache.clear()
        return node_id
    
    def node(self, nid: int) -> Node:
        """Get node by ID."""
        if nid not in self._nodes:
            raise ValueError(f"Node {nid} does not exist")
        return self._nodes[nid]
    
    def parents(self, nid: int) -> List[int]:
        """Get parent node IDs for a given node."""
        node = self.node(nid)  # Validates existence
        return list(node.inputs)
    
    def children(self, nid: int) -> List[int]:
        """Get child node IDs for a given node."""
        self.node(nid)  # Validates existence
        return self._children[nid].copy()
    
    def postorder(self, root: int) -> List[int]:
        """
        Get postorder traversal from root (parents before children).
        
        Uses DFS with memoization for efficiency. Result is deterministic.
        
        Args:
            root: Root node ID to traverse from
            
        Returns:
            List of node IDs in postorder (dependencies before dependents)
        """
        if root in self._postorder_cache:
            return self._postorder_cache[root]
        
        if root not in self._nodes:
            raise ValueError(f"Root node {root} does not exist")
        
        visited = set()
        result = []
        
        def dfs(node_id: int):
            if node_id in visited:
                return
            visited.add(node_id)
            
            node = self._nodes[node_id]
            # Visit parents first, sorted by ID for determinism
            parent_ids = sorted(node.inputs)
            for parent_id in parent_ids:
                dfs(parent_id)
            
            result.append(node_id)
        
        dfs(root)
        self._postorder_cache[root] = result
        return result
    
    def size(self) -> int:
        """Get total number of nodes in the DAG."""
        return len(self._nodes)
    
    def _serialize_meta(self, meta: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
        """Convert metadata dict to sorted tuple of string key-value pairs."""
        items = [(str(k), v) for k, v in meta.items()]
        return tuple(sorted(items))
    
    def _has_cycle(self, start: int) -> bool:
        """Check if the current graph has a cycle (after adding the new node)."""
        # Use DFS to detect cycles in the entire graph
        white = set(self._nodes.keys())  # Unvisited
        gray = set()   # In progress  
        black = set()  # Completed
        
        def dfs(node_id: int) -> bool:
            if node_id in black:
                return False
            if node_id in gray:
                return True  # Back edge found - cycle!
                
            gray.add(node_id)
            white.discard(node_id)
            
            # Follow outgoing edges (to children)
            for child_id in self._children[node_id]:
                if dfs(child_id):
                    return True
            
            gray.remove(node_id)
            black.add(node_id)
            return False
        
        # Check all components for cycles
        for node_id in list(white):
            if node_id in white:
                if dfs(node_id):
                    return True
        
        return False


# Optional torch integration
def _create_torch_dag_converter():
    """Create DAG converter for torch modules if torch is available."""
    try:
        import torch
        import torch.fx as fx
        
        def from_torch_module(module: torch.nn.Module, 
                            example_inputs: Tuple[Any, ...]) -> Tuple[DAG, int, Dict[int, Any]]:
            """
            Convert a torch module to a DAG using FX tracing.
            
            Args:
                module: PyTorch module to trace
                example_inputs: Example inputs for tracing
                
            Returns:
                Tuple of (DAG, root_id, input_mapping)
            """
            # Trace the module
            traced = fx.symbolic_trace(module)
            
            dag = DAG()
            node_map = {}
            inputs_dict = {}
            
            # Convert FX nodes to DAG nodes
            for fx_node in traced.graph.nodes:
                if fx_node.op == 'placeholder':
                    # Input node
                    node_id = dag.add_leaf(fx_node.name, {'fx_op': fx_node.op})
                    node_map[fx_node] = node_id
                    # Map example input if available
                    if len(example_inputs) > len(inputs_dict):
                        inputs_dict[node_id] = example_inputs[len(inputs_dict)]
                
                elif fx_node.op == 'call_function':
                    # Function call node
                    input_ids = [node_map[arg] for arg in fx_node.args if isinstance(arg, fx.Node)]
                    node_id = dag.add_op(
                        fx_node.name, 
                        fx_node.target,
                        input_ids,
                        {'fx_op': fx_node.op, 'fx_target': str(fx_node.target)}
                    )
                    node_map[fx_node] = node_id
                
                elif fx_node.op == 'output':
                    # Output node - return its input as root
                    if fx_node.args and isinstance(fx_node.args[0], fx.Node):
                        root_id = node_map[fx_node.args[0]]
                    else:
                        # Create a dummy output node
                        input_ids = [node_map[arg] for arg in fx_node.args if isinstance(arg, fx.Node)]
                        root_id = dag.add_op(fx_node.name, lambda x: x, input_ids, {'fx_op': fx_node.op})
            
            return dag, root_id, inputs_dict
        
        return from_torch_module
    
    except ImportError:
        return None


# Add torch conversion as a class method if available
_torch_converter = _create_torch_dag_converter()
if _torch_converter:
    DAG.from_torch_module = staticmethod(_torch_converter)