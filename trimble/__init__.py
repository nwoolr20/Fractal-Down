# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Trimble integration package for Fractal-Down.

This package demonstrates how Trimble (geospatial, construction, agriculture, 
transportation/logistics, positioning, and field/edge devices) can benefit from 
integrating Fractal-Down's √N-memory DAG engine with fractal priority scheduling, 
deterministic plans, and cached execution recipes.

Core integration areas:
- Geospatial & Survey/Mapping
- Construction (BIM + Field) 
- Digital Twins & Asset Lifecycle
- Precision Agriculture
- Autonomy & Guidance (Machine Control)
- Transportation & Logistics/Fleet & Telematics
- Mixed/Augmented Reality (Site Positioning & XR)
- UAV/Aerial Data Capture
"""

__version__ = "0.1.0"
__author__ = "Trimble Integration Team"

# Import key components
from . import examples
from . import scenarios  
from . import tests
from . import reports
from . import proposal_generator

__all__ = [
    "examples",
    "scenarios", 
    "tests",
    "reports",
    "proposal_generator"
]