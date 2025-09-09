# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""GPU kernel support placeholder."""

from __future__ import annotations

from . import features


def accelerate(data: str) -> str:
    """Mock acceleration using GPU kernels.

    Raises :class:`FeatureNotEnabledError` if GPU support is not enabled.
    """
    features.require_feature("GPU kernels", features.GPU_ENABLED)
    return f"accelerated {data} with GPU kernels"
