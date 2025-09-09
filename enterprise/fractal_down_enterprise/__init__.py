# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""Enterprise distribution for Fractal-Down.

Importing this package enables enterprise-only feature flags for the
base ``fractal_down`` package.
"""

from fractal_down.features import (
    enable_gpu,
    enable_distributed_planner,
    enable_visualization,
)

# Enable all enterprise features upon import.
enable_gpu()
enable_distributed_planner()
enable_visualization()
