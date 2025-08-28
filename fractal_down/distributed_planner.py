"""Distributed planning utilities placeholder."""

from __future__ import annotations

from .features import DISTRIBUTED_PLANNER_ENABLED, require_feature


def plan_dag(nodes: int) -> str:
    """Mock distributed planning.

    Raises :class:`ImportError` if the feature is not enabled.
    """
    require_feature("Distributed planner", DISTRIBUTED_PLANNER_ENABLED)
    return f"planned {nodes} nodes across cluster"
