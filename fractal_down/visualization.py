"""Visualization utilities placeholder."""

from __future__ import annotations

from .features import VISUALIZATION_ENABLED, require_feature


def render_dag(name: str) -> str:
    """Mock rendering of a DAG.

    Raises :class:`ImportError` if visualization is not enabled.
    """
    require_feature("Visualization", VISUALIZATION_ENABLED)
    return f"rendered visualization for {name}"
