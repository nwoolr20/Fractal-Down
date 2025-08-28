"""
Tests for Trimble integration examples.

Comprehensive test suite ensuring all Trimble domain examples work correctly
with Fractal-Down's √N memory DAG evaluation and priority scheduling.
"""

from .test_geospatial import *
from .test_construction import *
from .test_agriculture import *
from .test_autonomy import *
from .test_transportation import *
from .test_uav import *
from .test_mixed_reality import *
from .test_digital_twins import *

__all__ = [
    # Geospatial tests
    "test_lidar_processing_dag",
    "test_coordinate_transform_dag",
    "test_geospatial_demo",
    
    # Construction tests
    "test_bim_sync_dag",
    "test_deviation_detection_dag", 
    "test_construction_demo",
    
    # Agriculture tests
    "test_precision_agriculture_dag",
    "test_multi_machine_coordination_dag",
    "test_agriculture_demo",
    
    # Autonomy tests
    "test_safety_guidance_dag",
    "test_obstacle_detection_dag",
    "test_autonomy_demo",
    
    # Transportation tests
    "test_fleet_telematics_dag",
    "test_route_optimization_dag",
    "test_transportation_demo",
    
    # UAV tests
    "test_aerial_capture_dag",
    "test_flight_data_dag",
    "test_uav_demo",
    
    # Mixed Reality tests
    "test_spatial_anchoring_dag",
    "test_ar_overlay_dag", 
    "test_mixed_reality_demo",
    
    # Digital Twins tests
    "test_sensor_fusion_dag",
    "test_twin_update_dag",
    "test_digital_twin_demo"
]