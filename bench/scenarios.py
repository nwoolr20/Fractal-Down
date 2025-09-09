# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Benchmark scenarios for fractal-down evaluation.

Provides scenario providers that generate test jobs for baseline vs √N+fractal
comparison across different DAG structures and budgets.
"""

import math
import random
import operator
from typing import List, Dict, Any, Optional, Tuple
from collections import OrderedDict

from fractal_down.dag import DAG
from fractal_down.examples import make_tiny_dag


def _add_payload_to_inputs(inputs: Dict[int, Any], payload_bytes: int) -> Dict[int, Any]:
    """
    Replace input values with larger data structures to create memory pressure.
    
    Args:
        inputs: Original input dictionary 
        payload_bytes: Size of payload per input in bytes
        
    Returns:
        Modified inputs with payloads attached
    """
    if payload_bytes <= 0:
        return inputs
    
    # Create a large bytes object as payload
    # Use a simple pattern that compresses poorly to simulate real data
    try:
        import numpy as np
        # Use numpy arrays if available for more realistic memory usage
        # Each float64 is 8 bytes, so we need payload_bytes // 8 elements
        array_size = max(1, payload_bytes // 8)
        
        new_inputs = {}
        for node_id, orig_value in inputs.items():
            # Create payload array with some variation to prevent compression
            payload = np.random.rand(array_size).astype(np.float64)
            # Create a PayloadedValue wrapper that behaves like the original value
            new_inputs[node_id] = PayloadedValue(orig_value, payload)
        return new_inputs
        
    except ImportError:
        # Fallback to bytes if numpy not available
        # Create payload with some variation
        payload_template = bytes(range(256)) * (payload_bytes // 256 + 1)
        payload = payload_template[:payload_bytes]
        
        new_inputs = {}
        for node_id, orig_value in inputs.items():
            new_inputs[node_id] = PayloadedValue(orig_value, payload)
        return new_inputs


class PayloadedValue:
    """
    A wrapper that behaves like a numeric value but carries a large payload.
    
    This allows existing operations to work transparently while creating memory pressure.
    """
    
    def __init__(self, value, payload):
        self.value = value
        self.payload = payload
    
    def __add__(self, other):
        other_val = other.value if isinstance(other, PayloadedValue) else other
        result_val = self.value + other_val
        # Create new payload for result - make it bigger to show memory growth
        try:
            import numpy as np
            # Combine payloads and add some growth to simulate computation overhead
            self_size = len(self.payload)
            other_size = getattr(other, 'payload', [0]).__len__() if hasattr(getattr(other, 'payload', [0]), '__len__') else 0
            new_payload_size = max(self_size, other_size) + max(1000, self_size // 10)  # Add 10% growth + minimum
            new_payload = np.random.rand(new_payload_size).astype(np.float64)
            return PayloadedValue(result_val, new_payload)
        except ImportError:
            # Fallback to bytes-based payload growth
            self_size = len(self.payload) if hasattr(self.payload, '__len__') else 0
            other_size = getattr(other, 'payload', [0]).__len__() if hasattr(getattr(other, 'payload', [0]), '__len__') else 0
            new_size = max(self_size, other_size) + max(100, self_size // 10)  # Add 10% growth + minimum
            # Create payload with some variation
            payload_template = bytes(range(256)) * (new_size // 256 + 1)
            new_payload = payload_template[:new_size]
            return PayloadedValue(result_val, new_payload)
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __mul__(self, other):
        other_val = other.value if isinstance(other, PayloadedValue) else other
        result_val = self.value * other_val
        # Create new payload for result - make it bigger to show memory growth  
        try:
            import numpy as np
            self_size = len(self.payload)
            other_size = getattr(other, 'payload', [0]).__len__() if hasattr(getattr(other, 'payload', [0]), '__len__') else 0
            new_payload_size = max(self_size, other_size) + max(1000, self_size // 8)  # Add 12.5% growth + minimum
            new_payload = np.random.rand(new_payload_size).astype(np.float64)
            return PayloadedValue(result_val, new_payload)
        except ImportError:
            # Fallback to bytes-based payload growth
            self_size = len(self.payload) if hasattr(self.payload, '__len__') else 0
            other_size = getattr(other, 'payload', [0]).__len__() if hasattr(getattr(other, 'payload', [0]), '__len__') else 0
            new_size = max(self_size, other_size) + max(100, self_size // 8)  # Add 12.5% growth + minimum
            # Create payload with some variation
            payload_template = bytes(range(256)) * (new_size // 256 + 1)
            new_payload = payload_template[:new_size]
            return PayloadedValue(result_val, new_payload)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __sub__(self, other):
        other_val = other.value if isinstance(other, PayloadedValue) else other
        result_val = self.value - other_val
        return PayloadedValue(result_val, self.payload)
    
    def __rsub__(self, other):
        other_val = other if not isinstance(other, PayloadedValue) else other.value
        result_val = other_val - self.value
        return PayloadedValue(result_val, self.payload)
    
    def __truediv__(self, other):
        other_val = other.value if isinstance(other, PayloadedValue) else other
        result_val = self.value / other_val
        return PayloadedValue(result_val, self.payload)
    
    def __float__(self):
        return float(self.value)
    
    def __int__(self):
        return int(self.value)
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return f"PayloadedValue({self.value}, payload_len={len(self.payload) if hasattr(self.payload, '__len__') else 'N/A'})"


class Job:
    """A benchmark job specification."""
    
    def __init__(self, name: str, mode: str, budget_nodes: Optional[int], 
                 dag: DAG, root: int, inputs: Dict[int, Any], dwell_ms: int = 0):
        self.name = name
        self.mode = mode  # "baseline" or "sqrt"
        self.budget_nodes = budget_nodes  # None for baseline
        self.dag = dag
        self.root = root
        self.inputs = inputs
        self.dwell_ms = dwell_ms  # Time in milliseconds to keep memory alive after computation


def scenario_tiny(payload_bytes: int = 0, dwell_ms: int = 0) -> List[Job]:
    """
    Generate tiny scenario jobs using make_tiny_dag().
    
    Args:
        payload_bytes: Size of payload per node in bytes (0 = small numeric values)
        dwell_ms: Time in milliseconds to keep memory alive after computation
    
    Returns:
        List of Job objects for baseline and √N+fractal modes
        with budgets [2, 3] and 5 repeats each.
    """
    jobs = []
    budgets = [2, 3]
    repeats = 5
    
    # Get the tiny DAG
    dag, root, inputs = make_tiny_dag()
    
    # Modify inputs to include payload if requested
    if payload_bytes > 0:
        inputs = _add_payload_to_inputs(inputs, payload_bytes)
    
    # Baseline jobs (no budget limit, just topological evaluation)
    for repeat in range(repeats):
        job = Job(
            name=f"tiny/baseline/repeat_{repeat}",
            mode="baseline", 
            budget_nodes=None,
            dag=dag,
            root=root,
            inputs=inputs,
            dwell_ms=dwell_ms
        )
        jobs.append(job)
    
    # √N+fractal jobs with different budgets
    for budget in budgets:
        for repeat in range(repeats):
            job = Job(
                name=f"tiny/sqrt-{budget}/repeat_{repeat}",
                mode="sqrt",
                budget_nodes=budget,
                dag=dag,
                root=root,
                inputs=inputs,
                dwell_ms=dwell_ms
            )
            jobs.append(job)
    
    return jobs


def scenario_synthetic(n_nodes: int = 200, payload_bytes: int = 0, dwell_ms: int = 0) -> List[Job]:
    """
    Generate synthetic scenario with ~n_nodes DAG.
    
    Args:
        n_nodes: Target number of nodes in the synthetic DAG
        payload_bytes: Size of payload per node in bytes (0 = small numeric values)
        dwell_ms: Time in milliseconds to keep memory alive after computation
        
    Returns:
        List of Job objects for baseline and √N+fractal modes
        with computed budgets and 10 repeats each.
    """
    jobs = []
    repeats = 10
    
    # Create synthetic DAG
    dag, root, inputs = _create_synthetic_dag(n_nodes, payload_bytes)
    
    # Compute budgets: [ceil(sqrt(N))/2, ceil(sqrt(N)), 2*ceil(sqrt(N))]
    sqrt_n = math.ceil(math.sqrt(n_nodes))
    budgets = [
        max(1, sqrt_n // 2),  # Ensure at least 1
        sqrt_n,
        2 * sqrt_n
    ]
    
    # Baseline jobs
    for repeat in range(repeats):
        job = Job(
            name=f"synthetic-{n_nodes}/baseline/repeat_{repeat}",
            mode="baseline",
            budget_nodes=None,
            dag=dag,
            root=root,
            inputs=inputs,
            dwell_ms=dwell_ms
        )
        jobs.append(job)
    
    # √N+fractal jobs
    for budget in budgets:
        for repeat in range(repeats):
            job = Job(
                name=f"synthetic-{n_nodes}/sqrt-{budget}/repeat_{repeat}",
                mode="sqrt",
                budget_nodes=budget,
                dag=dag,
                root=root,
                inputs=inputs,
                dwell_ms=dwell_ms
            )
            jobs.append(job)
    
    return jobs


def _create_synthetic_dag(target_nodes: int, payload_bytes: int = 0, seed: int = 42) -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a synthetic DAG with approximately target_nodes nodes.
    
    The DAG will have bounded fan-in (<=3) and deterministic structure
    based on the seed. Nodes get random-but-deterministic metadata
    to exercise fractal priority computation.
    
    Args:
        target_nodes: Target number of nodes
        payload_bytes: Size of payload per input in bytes
        seed: Random seed for deterministic generation
        
    Returns:
        Tuple of (DAG, root_id, input_values)
    """
    random.seed(seed)
    dag = DAG()
    
    # Start with some leaf nodes (inputs)
    num_leaves = max(3, target_nodes // 8)  # ~12.5% leaves
    leaf_ids = []
    inputs = {}
    
    for i in range(num_leaves):
        # Random metadata for fractal priority
        meta = {
            "e": random.uniform(0.1, 1.0),
            "H": random.uniform(0.0, 1.0), 
            "w": random.uniform(0.1, 0.9),
            "n": random.uniform(0.1, 0.9),
            "a": random.uniform(0.0, 0.8)
        }
        
        leaf_id = dag.add_leaf(f"leaf_{i}", meta)
        leaf_ids.append(leaf_id)
        inputs[leaf_id] = random.uniform(-10.0, 10.0)
    
    # Add payload to inputs if requested
    if payload_bytes > 0:
        inputs = _add_payload_to_inputs(inputs, payload_bytes)
    
    # Define operations with their properties
    def double_op(x):
        return x * 2
    
    def inc_op(x):
        return x + 1
    
    def madd_op(x, y):
        return x * y + x
    
    # Build up layers of operations
    current_nodes = leaf_ids[:]
    operations = [
        (operator.add, "add", "binary"),
        (operator.mul, "mul", "binary"), 
        (operator.sub, "sub", "binary"),
        (double_op, "double", "unary"),
        (inc_op, "inc", "unary"),
        (madd_op, "madd", "binary")
    ]
    
    node_count = len(leaf_ids)
    layer = 0
    
    while node_count < target_nodes and len(current_nodes) > 0:
        layer += 1
        next_nodes = []
        
        # Randomly combine nodes from current layer
        random.shuffle(current_nodes)
        
        i = 0
        while i < len(current_nodes) and node_count < target_nodes:
            # Choose operation and fan-in
            op_func, op_name, op_type = random.choice(operations)
            
            # Determine number of inputs based on operation type
            if op_type == "unary":
                fan_in = 1
            elif op_type == "binary":
                fan_in = 2
            else:
                # Should not happen with current operations
                fan_in = 2
            
            # Adjust fan-in if we don't have enough nodes
            available = len(current_nodes) - i
            fan_in = min(fan_in, available)
                
            if fan_in == 0:
                break
                
            # For binary operations, ensure we have at least 2 nodes or skip
            if op_type == "binary" and fan_in < 2:
                # Try to use remaining nodes with add operation instead
                if available >= 2:
                    op_func = operator.add
                    op_name = "add"
                    fan_in = min(2, available)
                else:
                    # Skip this iteration
                    i += 1
                    continue
            
            # Get inputs for this operation
            op_inputs = current_nodes[i:i + fan_in]
            
            # Create metadata
            meta = {
                "e": random.uniform(0.2, 0.9),
                "H": random.uniform(0.1, 0.8),
                "w": random.uniform(0.2, 0.7),
                "n": random.uniform(0.0, 0.6),
                "a": random.uniform(0.1, 0.5)
            }
            
            try:
                node_id = dag.add_op(
                    f"op_{layer}_{len(next_nodes)}_{op_name}",
                    op_func,
                    op_inputs,
                    meta
                )
                next_nodes.append(node_id)
                node_count += 1
            except Exception as e:
                # If operation fails, skip it
                print(f"Warning: Skipping operation {op_name}: {e}")
                pass
            
            i += fan_in
        
        # If we couldn't create any new nodes, break
        if not next_nodes:
            break
            
        current_nodes = next_nodes
    
    # Choose root node (last layer, or create one if needed)
    if current_nodes:
        if len(current_nodes) == 1:
            root = current_nodes[0]
        else:
            # Combine remaining nodes into a root
            meta = {
                "e": 0.5,
                "H": 0.5,
                "w": 0.5,
                "n": 0.5,
                "a": 0.3
            }
            root = dag.add_op("root", operator.add, current_nodes, meta)
    else:
        # Fallback: use the first leaf as root
        root = leaf_ids[0]
    
    return dag, root, inputs


def scenario_memory_stress(payload_mb: int = 32, dwell_ms: int = 0) -> List[Job]:
    """
    Generate a memory stress scenario designed to cause baseline to fail while √space succeeds.
    
    This creates a DAG with large memory requirements that grows exponentially,
    designed to exceed memory limits with baseline evaluation but succeed with bounded √space.
    
    Args:
        payload_mb: Size of payload per node in MB (default 32MB for substantial pressure)
        dwell_ms: Time in milliseconds to keep memory alive after computation
        
    Returns:
        List of Job objects for baseline and √N+fractal modes
        with a small budget that should succeed while baseline fails.
    """
    jobs = []
    repeats = 10  # Increased for better variance reporting
    payload_bytes = payload_mb * 1024 * 1024  # Convert MB to bytes
    
    # Create a moderately sized DAG that will cause memory growth
    dag, root, inputs = _create_synthetic_dag(50, payload_bytes)  # 50 nodes with large payloads
    
    # Use a very small budget that should still work
    budget = 3  # Very constrained to demonstrate √space benefits
    
    # Baseline jobs (will likely exceed memory with large payloads)  
    for repeat in range(repeats):
        job = Job(
            name=f"memory-stress-{payload_mb}mb/baseline/repeat_{repeat}",
            mode="baseline",
            budget_nodes=None,
            dag=dag,
            root=root,
            inputs=inputs,
            dwell_ms=dwell_ms
        )
        jobs.append(job)
    
    # √N+fractal jobs with small budget (should succeed with bounded memory)
    for repeat in range(repeats):
        job = Job(
            name=f"memory-stress-{payload_mb}mb/sqrt-{budget}/repeat_{repeat}",
            mode="sqrt", 
            budget_nodes=budget,
            dag=dag,
            root=root,
            inputs=inputs,
            dwell_ms=dwell_ms
        )
        jobs.append(job)
    
    return jobs