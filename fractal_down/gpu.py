"""GPU kernel support placeholder."""

from __future__ import annotations

from .features import GPU_ENABLED, require_feature


def accelerate(data: str) -> str:
    """Mock acceleration using GPU kernels.

    Raises :class:`ImportError` if GPU support is not enabled.
    """
    require_feature("GPU kernels", GPU_ENABLED)
    return f"accelerated {data} with GPU kernels"
