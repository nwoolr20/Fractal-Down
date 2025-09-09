# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Fractal priority computation for fractal-down.

Implements the energy-based priority system with depth-dependent thresholds
and constraint propagation to ensure parents have higher priority than children.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Mapping, Optional, Any
from fractal_down.dag import DAG
import math


@dataclass
class FractalParams:
    """Parameters for fractal priority computation."""

    alpha: float = 1.0  # residual/error weight
    beta: float = 0.6  # entropy/spread weight
    gamma: float = 0.8  # affect weight
    delta: float = 0.5  # novelty weight
    kappa: float = 0.4  # age penalty weight
    tau0: float = 0.25  # base threshold
    lambda_: float = 0.7  # geometric schedule param
    p: Optional[float] = None  # if set, tau = tau0 / (s+1)^p else tau0 * lambda_^s

    def asdict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


def compute_node_priority(
    dag: DAG, root: int, params: Optional[FractalParams] = None
) -> Dict[int, float]:
    """
    Compute fractal priority for all nodes reachable from root.

    Uses energy function E = αe + βH + γw + δn - κa where:
    - e: residual/error (meta key "e")
    - H: entropy/spread (meta key "H" or "h")
    - w: affect weight (meta key "w")
    - n: novelty (meta key "n")
    - a: age (meta key "a")

    Priority = max(0, E - τ_s) where τ_s is depth-dependent threshold.
    Results are normalized to [0,1] and parent priority >= child priority is enforced.
    Inputs get minimum priority of 0.05.

    Args:
        dag: The DAG to compute priorities for
        root: Root node ID
        params: Fractal parameters (uses defaults if None)

    Returns:
        Dict mapping node ID to priority in [0,1]
    """
    if params is None:
        params = FractalParams()

    # Get all reachable nodes in postorder
    reachable = dag.postorder(root)

    # Compute depths
    depths = _compute_depths(dag, reachable)

    # Compute raw energy scores
    raw_scores = {}
    for node_id in reachable:
        node = dag.node(node_id)

        # Extract energy components from meta, defaulting to 0.0
        meta_dict = dict(node.meta)
        e = float(meta_dict.get("e", 0.0))
        H = float(
            meta_dict.get("H", meta_dict.get("h", 0.0))
        )  # Support both "H" and "h"
        w = float(meta_dict.get("w", 0.0))
        n = float(meta_dict.get("n", 0.0))
        a = float(meta_dict.get("a", 0.0))

        # Compute energy
        energy = (
            params.alpha * e
            + params.beta * H
            + params.gamma * w
            + params.delta * n
            - params.kappa * a
        )

        # Compute depth-dependent threshold
        depth = depths[node_id]
        if params.p is not None:
            threshold = params.tau0 / ((depth + 1) ** params.p)
        else:
            threshold = params.tau0 * (params.lambda_**depth)

        # Raw score = max(0, E - τ_s)
        raw_scores[node_id] = max(0.0, energy - threshold)

    # Normalize scores to [0,1]
    max_score = max(raw_scores.values()) if raw_scores else 0.0
    if max_score > 0:
        normalized = {nid: score / max_score for nid, score in raw_scores.items()}
    else:
        normalized = {nid: 0.0 for nid in raw_scores}

    # Enforce parent priority >= child priority constraint
    priorities = _enforce_parent_child_constraint(dag, reachable, normalized)

    # Ensure inputs have minimum priority of 0.05
    for node_id in reachable:
        node = dag.node(node_id)
        if node.op is None:  # Leaf/input node
            priorities[node_id] = max(priorities[node_id], 0.05)

    return priorities


def _compute_depths(dag: DAG, nodes: list[int]) -> Dict[int, int]:
    """
    Compute depth for each node (inputs have depth 0).

    Args:
        dag: The DAG
        nodes: List of node IDs to compute depths for

    Returns:
        Dict mapping node ID to depth
    """
    depths = {}

    # Process nodes in topological order (postorder gives us this)
    for node_id in nodes:
        node = dag.node(node_id)

        if not node.inputs:  # Input/leaf node
            depths[node_id] = 0
        else:
            # Depth = 1 + max(parent depths)
            # Sort parents by id for determinism when depths are equal
            parent_depths = []
            for parent_id in sorted(node.inputs):
                if parent_id in depths:
                    parent_depths.append(depths[parent_id])
                else:
                    # Parent should have been processed already in postorder
                    # If not, it means there's a cycle or the node is not reachable
                    parent_depths.append(0)

            depths[node_id] = 1 + max(parent_depths) if parent_depths else 0

    return depths


def _enforce_parent_child_constraint(
    dag: DAG, nodes: list[int], priorities: Dict[int, float]
) -> Dict[int, float]:
    """
    Enforce that parent priority >= child priority.

    Propagates priority upward from children to parents iteratively
    until convergence.

    Args:
        dag: The DAG
        nodes: List of node IDs
        priorities: Initial priority mapping

    Returns:
        Updated priority mapping satisfying parent >= child constraint
    """
    result = priorities.copy()

    # Iteratively propagate constraints upward
    # Process in reverse postorder (children before parents)
    changed = True
    max_iterations = len(nodes) * 2  # Prevent infinite loops
    iteration = 0

    while changed and iteration < max_iterations:
        changed = False
        iteration += 1

        # Process nodes in reverse postorder (children first)
        for node_id in reversed(nodes):
            node = dag.node(node_id)

            # For each parent, ensure parent priority >= this node's priority
            for parent_id in node.inputs:
                if parent_id in result:
                    old_parent_priority = result[parent_id]
                    new_parent_priority = max(result[parent_id], result[node_id])
                    if new_parent_priority > old_parent_priority:
                        result[parent_id] = new_parent_priority
                        changed = True

    return result
