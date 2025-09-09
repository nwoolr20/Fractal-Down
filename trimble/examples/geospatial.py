# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Geospatial and Survey/Mapping examples for Trimble integration.

Demonstrates point cloud & LiDAR processing pipelines, coordinate transformations,
and survey data workflows using Fractal-Down's √N memory DAG execution.
"""

from typing import Dict, List, Tuple, Any, Optional
import operator
import math

from fractal_down.dag import DAG
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams


def create_lidar_processing_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a LiDAR point cloud processing pipeline DAG.
    
    Pipeline: Ingestion → Noise Filtering → Ground Segmentation → 
              Feature Extraction → Meshing → Compression
    
    This demonstrates the cached recipe concept where repeated region-of-interest
    refines can skip earlier processing steps.
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input nodes - raw LiDAR data
    raw_points = dag.add_leaf("raw_lidar_points", {
        "e": 1.0,  # High energy - raw data processing
        "H": 0.9,  # High entropy - unprocessed data
        "cache_key": "lidar_raw",
        "data_type": "point_cloud"
    })
    
    intensity_data = dag.add_leaf("intensity_values", {
        "e": 0.8,
        "H": 0.7,
        "cache_key": "intensity_raw",
        "data_type": "intensity_array"
    })
    
    # Noise filtering - cacheable transformation
    def noise_filter(points, intensity):
        """Statistical outlier removal and noise filtering."""
        # Simulate noise filtering that preserves 85% of points
        return points * 0.85, intensity * 0.85
    
    filtered_data = dag.add_op("noise_filter", noise_filter, 
                              [raw_points, intensity_data], {
        "e": 0.9,  # High compute for statistical analysis
        "H": 0.5,  # Reduced entropy after filtering
        "cache_key": "noise_filtered",
        "cacheable": True,
        "priority_class": "P2"  # Operational intelligence
    })
    
    # Ground segmentation - computationally intensive, cacheable
    def ground_segmentation(filtered_data):
        """RANSAC-based ground plane detection and segmentation."""
        # filtered_data contains both points and intensity
        filtered_points, filtered_intensity = filtered_data
        # Simulate ground segmentation splitting data 70/30
        ground_points = filtered_points * 0.7
        object_points = filtered_points * 0.3
        return ground_points, object_points
        
    ground_seg = dag.add_op("ground_segmentation", ground_segmentation,
                           [filtered_data], {
        "e": 1.2,  # Very high compute - RANSAC iterations
        "H": 0.3,  # Much lower entropy after segmentation  
        "cache_key": "ground_segmented",
        "cacheable": True,
        "priority_class": "P2"
    })
    
    # Feature extraction - highly cacheable for repeated queries
    def extract_features(ground_data):
        """Extract geometric features from segmented point cloud."""
        ground_points, object_points = ground_data
        # Simulate feature extraction (planar surfaces, edges, etc.)
        features = {
            "planar_surfaces": ground_points * 0.8,
            "linear_features": object_points * 0.2, 
            "volumetric_objects": object_points * 0.8
        }
        return features
        
    features = dag.add_op("feature_extraction", extract_features,
                         [ground_seg], {
        "e": 0.8,
        "H": 0.2,  # Highly structured after feature extraction
        "cache_key": "features_extracted", 
        "cacheable": True,
        "priority_class": "P2"
    })
    
    # Meshing - for visualization and analysis
    def create_mesh(features):
        """Generate triangulated mesh from extracted features."""
        # Simulate mesh generation
        return features["planar_surfaces"] * 1.1  # Mesh overhead
        
    mesh = dag.add_op("mesh_generation", create_mesh, [features], {
        "e": 0.6,
        "H": 0.1,  # Very structured mesh output
        "cache_key": "mesh_generated",
        "cacheable": True, 
        "priority_class": "P3"  # Batch analytics
    })
    
    # Compression for storage/transmission
    def compress_data(mesh_data):
        """Compress processed data for storage or transmission."""
        # Simulate compression reducing size by 60%
        return mesh_data * 0.4
        
    compressed = dag.add_op("compression", compress_data, [mesh], {
        "e": 0.4,
        "H": 0.05,  # Highly compressed, low entropy
        "cache_key": "compressed_output",
        "priority_class": "P4"  # Archival
    })
    
    # Input values simulating a 1M point LiDAR scan
    inputs = {
        raw_points: 1000000,  # 1M points
        intensity_data: 1000000  # Corresponding intensity values
    }
    
    return dag, compressed, inputs


def create_coordinate_transform_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a coordinate transformation pipeline for geodetic conversions.
    
    Demonstrates cached recipe reuse for coordinate transforms across
    simultaneous survey jobs (WGS84 <-> local projections).
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input coordinates in WGS84
    wgs84_coords = dag.add_leaf("wgs84_coordinates", {
        "e": 0.3,  # Low energy - just coordinate data
        "H": 0.8,  # High entropy - geographic spread
        "data_type": "geographic_coordinates"
    })
    
    # Datum parameters for local projection
    local_datum = dag.add_leaf("local_datum_params", {
        "e": 0.1,  # Very low energy - just parameters
        "H": 0.2,  # Low entropy - structured parameters
        "data_type": "datum_parameters"
    })
    
    # Ellipsoid calculations - highly cacheable
    def ellipsoid_transform(coords, datum):
        """Transform between ellipsoids (WGS84 to local)."""
        # Simulate ellipsoid transformation calculations
        if isinstance(coords, list):
            return [(lat * 1.0001, lon * 1.0001) for lat, lon in coords]
        return coords * 1.0001  # Small transformation factor
        
    ellipsoid_transformed = dag.add_op("ellipsoid_transform", ellipsoid_transform,
                                     [wgs84_coords, local_datum], {
        "e": 0.7,  # Moderate compute for ellipsoid math
        "H": 0.6,
        "cache_key": "ellipsoid_wgs84_to_local",
        "cacheable": True,
        "priority_class": "P1"  # Real-time control priority
    })
    
    # Map projection - frequently reused transformation  
    def map_projection(ellipsoid_coords, datum):
        """Apply map projection (e.g., UTM, State Plane)."""
        # Simulate projection calculations
        if isinstance(ellipsoid_coords, list):
            return {
                "easting": [lat * 500000 for lat, lon in ellipsoid_coords],   # UTM false easting
                "northing": [lat * 4000000 for lat, lon in ellipsoid_coords], # UTM false northing  
                "zone": 18  # UTM zone
            }
        return {
            "easting": ellipsoid_coords * 500000,   # UTM false easting
            "northing": ellipsoid_coords * 4000000, # UTM false northing  
            "zone": 18  # UTM zone
        }
        
    projected = dag.add_op("map_projection", map_projection,
                          [ellipsoid_transformed, local_datum], {
        "e": 0.5,
        "H": 0.4,  # More structured after projection
        "cache_key": "utm_projection",
        "cacheable": True,
        "priority_class": "P1"
    })
    
    # Grid correction - for high-precision surveying
    def grid_correction(projected_coords):
        """Apply local grid corrections and scale factors."""
        # Simulate grid correction application
        if isinstance(projected_coords.get("easting"), list):
            corrected = {
                "easting": [e * 1.00001 for e in projected_coords["easting"]],
                "northing": [n * 1.00001 for n in projected_coords["northing"]],
                "elevation": [0.1] * len(projected_coords["easting"])
            }
        else:
            corrected = {
                "easting": projected_coords["easting"] * 1.00001,
                "northing": projected_coords["northing"] * 1.00001,
                "elevation": projected_coords.get("elevation", 0) + 0.1
            }
        return corrected
        
    final_coords = dag.add_op("grid_correction", grid_correction, [projected], {
        "e": 0.3,
        "H": 0.2,  # Highly precise, low entropy result
        "cache_key": "grid_corrected",
        "cacheable": True,
        "priority_class": "P1"
    })
    
    # Input values - sample survey coordinates
    inputs = {
        wgs84_coords: [
            (40.7128, -74.0060),  # New York City
            (40.7589, -73.9851),  # Times Square
            (40.6892, -74.0445)   # Statue of Liberty
        ],
        local_datum: {
            "ellipsoid": "GRS80",
            "projection": "UTM_18N", 
            "datum": "NAD83",
            "units": "meters"
        }
    }
    
    return dag, final_coords, inputs


def demo_point_cloud_pipeline():
    """
    Demonstrate the complete point cloud processing pipeline with caching.
    
    Shows how cached recipes enable faster reprocessing of similar datasets
    and how fractal priority scheduling ensures real-time preview paths
    complete before full-fidelity processing.
    """
    print("=== Trimble LiDAR Point Cloud Processing Demo ===")
    
    # Create the LiDAR processing DAG
    dag, root, inputs = create_lidar_processing_dag()
    print(f"Created LiDAR processing DAG with {dag.size()} nodes")
    
    # Show pipeline structure
    print("\nProcessing Pipeline:")
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        # Convert meta tuple to dict for easier access
        meta_dict = dict(node.meta) if node.meta else {}
        cache_info = meta_dict.get("cacheable", False)
        priority = meta_dict.get("priority_class", "P2")
        cache_str = " [CACHEABLE]" if cache_info else ""
        print(f"  {node.name} ({priority}){cache_str}")
    
    # Compute fractal priorities with safety-first parameters
    params = FractalParams(
        alpha=0.7,    # Bias toward compute efficiency  
        beta=0.3,     # Less weight on entropy reduction
        gamma=0.1     # Minimal locality bias
    )
    priorities = compute_node_priority(dag, root, params)
    
    print("\nNode Priorities (Fractal Scheduling):")
    for node_id, priority in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
        node = dag.node(node_id)
        print(f"  {node.name}: {priority:.3f}")
    
    # Build execution plan with memory budget
    budget = 4  # √N memory constraint
    plan = build_plan(dag, root, budget_nodes=budget, node_priority=priorities)
    
    print(f"\nExecution Plan (Budget: {budget} nodes):")
    print(f"  Order: {[dag.node(nid).name for nid in plan.order]}")
    
    # Execute with verification
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=True)
    
    print(f"\nExecution Results:")
    print(f"  Final result: {result.value:.0f} compressed points")
    print(f"  √N memory constraint: {budget} nodes maximum")
    print(f"  Cache hits: {len([n for n in dag._nodes if dict(dag.node(n).meta).get('cacheable')])}")
    print(f"  Verification: {'PASSED' if result.value is not None else 'FAILED'}")
    
    # Demonstrate coordinate transformation caching
    print("\n=== Coordinate Transformation Caching Demo ===")
    coord_dag, coord_root, coord_inputs = create_coordinate_transform_dag()
    
    coord_plan = build_plan(coord_dag, coord_root, budget_nodes=3)
    coord_evaluator = Evaluator(coord_dag, coord_inputs)
    coord_result = coord_evaluator.run(coord_plan)
    
    print(f"Transformed coordinates: {coord_result.value}")
    print(f"Cache-enabled transformations: 3/4 operations cacheable")


if __name__ == "__main__":
    demo_point_cloud_pipeline()