# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
DAG evaluator with √N memory constraint for fractal-down.

Executes plans with LRU caching and recomputation, supporting verification
and deterministic tensor hashing when torch is available.
"""

from collections import OrderedDict
from typing import Any, Dict, Mapping, NamedTuple, Optional
import hashlib

from fractal_down.dag import DAG
from fractal_down.treelift import Plan
from fractal_down.hashing import HashProvider, get_default_provider


class EvalResult(NamedTuple):
    """Result of DAG evaluation."""

    value: Any
    digest: bytes


class Evaluator:
    """
    DAG evaluator with √N memory constraint.

    Executes plans using an LRU cache with the specified budget,
    recomputing evicted nodes as needed.
    """

    def __init__(
        self,
        dag: DAG,
        inputs: Mapping[int, Any],
        hash_provider: Optional[HashProvider] = None,
    ):
        """
        Initialize evaluator.

        Args:
            dag: DAG to evaluate
            inputs: Mapping from input node IDs to their values
            hash_provider: Hash provider for digest computation
        """
        self.dag = dag
        self.inputs = dict(inputs)  # Copy to avoid mutation
        self.hash_provider = hash_provider or get_default_provider()

        # Validate that all input nodes exist and are leaves
        for input_id in self.inputs:
            node = self.dag.node(input_id)  # Validates existence
            if node.op is not None:
                raise ValueError(f"Input node {input_id} is not a leaf node")

    def run(self, plan: Plan, verify: bool = False) -> EvalResult:
        """
        Execute the given plan.

        Args:
            plan: Execution plan to run
            verify: If True, recompute root and verify digest matches

        Returns:
            EvalResult with final value and digest

        Raises:
            ValueError: If verification fails or required inputs are missing
        """
        if plan.root not in self.dag._nodes:
            raise ValueError(f"Plan root {plan.root} not found in DAG")

        # Initialize LRU cache for computed values
        cache: OrderedDict[int, Any] = OrderedDict()

        # Execute each node in the plan order
        for node_id in plan.order:
            if node_id in cache:
                # Already computed, move to end (most recent)
                cache.move_to_end(node_id)
            else:
                # Need to compute this node
                value = self._compute_node(node_id, cache, plan.budget_nodes)
                cache[node_id] = value

                # Evict LRU nodes if over budget
                while len(cache) > plan.budget_nodes:
                    cache.popitem(last=False)

        # Get final result - root should be in cache or recompute if evicted
        if plan.root in cache:
            root_value = cache[plan.root]
        else:
            root_value = self._compute_node(plan.root, cache, plan.budget_nodes)

        # Compute digest
        digest = self._compute_digest(root_value)
        result = EvalResult(root_value, digest)

        # Verification: recompute root independently and check digest
        if verify:
            # Clear cache and recompute root
            verification_cache: OrderedDict[int, Any] = OrderedDict()
            verified_value = self._compute_node(
                plan.root, verification_cache, plan.budget_nodes
            )
            verified_digest = self._compute_digest(verified_value)

            if verified_digest != digest:
                raise ValueError(
                    f"Verification failed: digest mismatch. "
                    f"Expected {digest.hex()}, got {verified_digest.hex()}"
                )

        return result

    def _compute_node(
        self, node_id: int, cache: OrderedDict[int, Any], budget: int
    ) -> Any:
        """
        Compute value for a single node.

        Args:
            node_id: Node to compute
            cache: Current cache of computed values
            budget: Cache budget for eviction control

        Returns:
            Computed value for the node
        """
        node = self.dag.node(node_id)

        if node.op is None:
            # Leaf node - get from inputs
            if node_id not in self.inputs:
                raise ValueError(
                    f"Missing input value for leaf node {node_id} ({node.name})"
                )
            return self.inputs[node_id]

        # Operation node - get parent values
        parent_values = []
        for parent_id in node.inputs:
            parent_value = self._get_value(parent_id, cache, budget)
            parent_values.append(parent_value)

        # Apply operation
        return node.op(*parent_values)

    def _get_value(
        self, node_id: int, cache: OrderedDict[int, Any], budget: int
    ) -> Any:
        """Get value for a node, using cache or recomputing."""
        if node_id in cache:
            # Found in cache, move to end
            cache.move_to_end(node_id)
            return cache[node_id]

        # Not in cache - need to recompute
        value = self._compute_node(node_id, cache, budget)
        cache[node_id] = value

        # Evict LRU if over budget
        while len(cache) > budget:
            cache.popitem(last=False)

        return value

    def _compute_digest(self, value: Any) -> bytes:
        """
        Compute hash digest for a value.

        Handles torch tensors specially if torch is available,
        otherwise uses repr() for string representation.
        """
        try:
            import torch

            if isinstance(value, torch.Tensor):
                # For tensors, use detached, contiguous numpy bytes
                tensor_bytes = value.detach().cpu().contiguous().numpy().tobytes()
                return self.hash_provider.digest(tensor_bytes)
        except ImportError:
            pass

        # Default: use string representation
        value_str = repr(value)
        return self.hash_provider.digest(value_str.encode("utf-8"))
