"""
√N TreeLift Plan builder for fractal-down.

Implements the TreeLift algorithm that simulates evaluation with an LRU cache
to build execution plans with square-root memory complexity.
"""

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple
from collections import OrderedDict
import math

from fractal_down.dag import DAG


@dataclass(frozen=True)
class Plan:
    """Execution plan for DAG evaluation with √N memory constraint."""
    root: int
    budget_nodes: int
    order: Tuple[int, ...]  # evaluation sequence with repeats allowed


def build_plan(dag: DAG, root: int, budget_nodes: Optional[int] = None, 
               node_priority: Optional[Mapping[int, float]] = None) -> Plan:
    """
    Build a √N TreeLift execution plan for the given DAG.
    
    Simulates evaluation with an LRU cache to determine which nodes need
    to be computed/recomputed and in what order.
    
    Args:
        dag: The DAG to build a plan for
        root: Root node ID to evaluate
        budget_nodes: Maximum cache size (defaults to √N)
        node_priority: Priority mapping for parent ordering (higher = earlier)
        
    Returns:
        Plan with execution order respecting dependencies and budget
    """
    # Validate root exists
    dag.node(root)  # Raises if root doesn't exist
    
    # Compute default budget if not provided
    if budget_nodes is None:
        postorder_nodes = dag.postorder(root)
        budget_nodes = max(16, math.ceil(math.sqrt(len(postorder_nodes))))
    
    # Initialize priority mapping with defaults if not provided
    if node_priority is None:
        # Default priority: all nodes equal, leaves slightly higher
        postorder_nodes = dag.postorder(root)
        node_priority = {}
        for nid in postorder_nodes:
            node = dag.node(nid)
            node_priority[nid] = 0.1 if node.op is None else 0.0
    
    # Build the plan using TreeLift algorithm
    builder = _PlanBuilder(dag, budget_nodes, node_priority)
    order = builder.ensure(root)
    
    return Plan(
        root=root,
        budget_nodes=budget_nodes,
        order=tuple(order)
    )


class _PlanBuilder:
    """Internal helper for building TreeLift plans."""
    
    def __init__(self, dag: DAG, budget_nodes: int, node_priority: Mapping[int, float]):
        self.dag = dag
        self.budget_nodes = budget_nodes
        self.node_priority = node_priority
        self.cache: OrderedDict[int, bool] = OrderedDict()  # LRU cache simulation
        self.order: List[int] = []  # Execution order being built
    
    def ensure(self, node_id: int) -> List[int]:
        """
        Ensure node is available, recursively ensuring parents first.
        
        Implements the core TreeLift algorithm:
        1. If node is cached, move to end (most recent)
        2. Otherwise, ensure parents in priority order, emit node, cache it
        3. Evict LRU nodes if over budget
        
        Args:
            node_id: Node to ensure is available
            
        Returns:
            Complete execution order list
        """
        self._ensure_recursive(node_id)
        return self.order
    
    def _ensure_recursive(self, node_id: int):
        """Recursive helper for ensure()."""
        
        # If already cached, move to end (mark as most recently used)
        if node_id in self.cache:
            self.cache.move_to_end(node_id)
            return
        
        # Node not cached - need to compute it
        node = self.dag.node(node_id)
        
        # First ensure all parents are available
        if node.inputs:
            # Sort parents by priority (descending) then by ID (ascending) for determinism
            parents_with_priority = [
                (self.node_priority.get(pid, 0.0), pid) 
                for pid in node.inputs
            ]
            # Sort by priority descending, then by ID ascending for tie-breaking
            parents_with_priority.sort(key=lambda x: (-x[0], x[1]))
            
            # Recursively ensure parents in priority order
            for _, parent_id in parents_with_priority:
                self._ensure_recursive(parent_id)
        
        # Re-ensure any parents that might have been evicted
        # (This is the key insight: we need to check parent availability again)
        if node.inputs:
            for parent_id in node.inputs:
                if parent_id not in self.cache:
                    # Parent was evicted, need to recompute
                    self._ensure_recursive(parent_id)
        
        # Emit this node to the execution order
        self.order.append(node_id)
        
        # Add to cache (mark as most recently used)
        self.cache[node_id] = True
        
        # Evict LRU nodes if over budget
        while len(self.cache) > self.budget_nodes:
            # Remove least recently used (first item)
            self.cache.popitem(last=False)