# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""Feature flag utilities for optional enterprise components."""

from __future__ import annotations

import os


class FeatureNotEnabledError(Exception):
    """Raised when an enterprise feature is used but not enabled."""
    pass

_GPU_ENV = "FRACTAL_DOWN_GPU"
_DISTRIBUTED_ENV = "FRACTAL_DOWN_DISTRIBUTED"
_VIZ_ENV = "FRACTAL_DOWN_VIZ"


def _get_flag(name: str) -> bool:
    """Return ``True`` if the environment variable ``name`` is set to ``"1"``."""
    return os.getenv(name, "0") == "1"


GPU_ENABLED = _get_flag(_GPU_ENV)
"""Whether GPU kernel support is enabled."""

DISTRIBUTED_PLANNER_ENABLED = _get_flag(_DISTRIBUTED_ENV)
"""Whether the distributed planner is enabled."""

VISUALIZATION_ENABLED = _get_flag(_VIZ_ENV)
"""Whether visualization utilities are enabled."""


def enable_gpu() -> None:
    """Enable GPU kernel support for the current process."""
    os.environ[_GPU_ENV] = "1"
    global GPU_ENABLED
    GPU_ENABLED = True


def enable_distributed_planner() -> None:
    """Enable the distributed planner for the current process."""
    os.environ[_DISTRIBUTED_ENV] = "1"
    global DISTRIBUTED_PLANNER_ENABLED
    DISTRIBUTED_PLANNER_ENABLED = True


def enable_visualization() -> None:
    """Enable visualization utilities for the current process."""
    os.environ[_VIZ_ENV] = "1"
    global VISUALIZATION_ENABLED
    VISUALIZATION_ENABLED = True


def require_feature(name: str, enabled: bool) -> None:
    """Raise :class:`FeatureNotEnabledError` if ``enabled`` is ``False``.

    Parameters
    ----------
    name:
        Human-readable name of the feature for error messages.
    enabled:
        Boolean flag indicating whether the feature is active.
    """
    if not enabled:
        raise FeatureNotEnabledError(
            f"{name} requires the enterprise edition. Please upgrade to access this feature."
        )
