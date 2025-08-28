"""Distributed planning utilities placeholder."""

from __future__ import annotations

from . import features


def plan_dag(nodes: int) -> str:
    """Mock distributed planning.

    Raises :class:`FeatureNotEnabledError` if the feature is not enabled.
    """
    features.require_feature("Distributed planner", features.DISTRIBUTED_PLANNER_ENABLED)
    return f"planned {nodes} nodes across cluster"
