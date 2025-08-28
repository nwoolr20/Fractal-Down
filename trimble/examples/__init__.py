"""
Trimble examples showcasing Fractal-Down integration across various domains.

This module provides practical examples of how Trimble's various business segments
can leverage Fractal-Down's capabilities for improved performance and efficiency.
"""

from .geospatial import *
from .construction import *
from .agriculture import *
from .autonomy import *
from .transportation import *
from .uav import *
from .mixed_reality import *
from .digital_twins import *

__all__ = [
    # Geospatial exports
    "create_lidar_processing_dag",
    "create_coordinate_transform_dag", 
    "demo_point_cloud_pipeline",
    
    # Construction exports
    "create_bim_sync_dag",
    "create_deviation_detection_dag",
    "demo_incremental_bim_sync",
    
    # Agriculture exports
    "create_precision_agriculture_dag",
    "create_multi_machine_coordination_dag",
    "demo_field_processing_pipeline",
    
    # Autonomy exports
    "create_safety_guidance_dag",
    "create_obstacle_detection_dag",
    "demo_autonomous_assistance",
    
    # Transportation exports  
    "create_fleet_telematics_dag",
    "create_route_optimization_dag",
    "demo_logistics_pipeline",
    
    # UAV exports
    "create_aerial_capture_dag",
    "create_flight_data_dag", 
    "demo_uav_processing",
    
    # Mixed Reality exports
    "create_spatial_anchoring_dag",
    "create_ar_overlay_dag",
    "demo_mixed_reality_pipeline",
    
    # Digital Twins exports
    "create_sensor_fusion_dag",
    "create_twin_update_dag",
    "demo_digital_twin_sync"
]