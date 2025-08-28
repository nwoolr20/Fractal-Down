"""
Trimble scenarios demonstrating real-world workflows and use cases.

This package provides concrete scenarios showing how Fractal-Down integrates
with Trimble's various business segments and operational workflows.
"""

from .construction_site_scenario import *
from .precision_agriculture_scenario import *
from .survey_mapping_scenario import *
from .fleet_telematics_scenario import *
from .edge_deployment_scenario import *

__all__ = [
    "construction_site_workflow",
    "precision_agriculture_workflow", 
    "survey_mapping_workflow",
    "fleet_telematics_workflow",
    "edge_deployment_workflow",
    "run_all_scenarios"
]