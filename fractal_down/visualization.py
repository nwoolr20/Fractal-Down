"""Visualization utilities placeholder."""

from __future__ import annotations

from . import features


def render_dag(name: str) -> str:
    """Mock rendering of a DAG.

    Raises :class:`FeatureNotEnabledError` if visualization is not enabled.
    """
    features.require_feature("Visualization", features.VISUALIZATION_ENABLED)
    return f"rendered visualization for {name}"
