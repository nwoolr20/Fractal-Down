# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Tests for Trimble geospatial and survey/mapping examples.

Validates LiDAR processing, coordinate transformations, and caching behavior.
"""

import pytest
from trimble.examples.geospatial import (
    create_lidar_processing_dag,
    create_coordinate_transform_dag,
    demo_point_cloud_pipeline
)
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams


def test_lidar_processing_dag():
    """Test LiDAR point cloud processing DAG creation and execution."""
    dag, root, inputs = create_lidar_processing_dag()
    
    # Validate DAG structure
    assert dag.size() > 0
    assert root in dag._nodes
    assert len(inputs) > 0
    
    # Check that we have the expected pipeline stages
    node_names = [dag.node(nid).name for nid in dag._nodes]
    expected_stages = [
        "raw_lidar_points", "intensity_values", "noise_filter",
        "ground_segmentation", "feature_extraction", "mesh_generation", "compression"
    ]
    
    for stage in expected_stages:
        assert stage in node_names, f"Missing expected pipeline stage: {stage}"
    
    # Test execution with small budget
    plan = build_plan(dag, root, budget_nodes=3)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_lidar_processing_with_priorities():
    """Test LiDAR processing with fractal priority scheduling."""
    dag, root, inputs = create_lidar_processing_dag()
    
    # Compute priorities with geospatial-specific parameters
    params = FractalParams(alpha=0.7, beta=0.3, gamma=0.1, min_priority=0.05)
    priorities = compute_node_priority(dag, root, params)
    
    # Verify all nodes have priorities
    assert len(priorities) == dag.size()
    assert all(0.0 <= p <= 1.0 for p in priorities.values())
    
    # Build plan with priorities
    plan = build_plan(dag, root, budget_nodes=4, node_priority=priorities)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=True)
    
    assert result.value is not None


def test_lidar_caching_behavior():
    """Test that cacheable transformations are properly marked."""
    dag, root, inputs = create_lidar_processing_dag()
    
    # Count cacheable nodes
    cacheable_nodes = []
    for node_id in dag._nodes:
        node = dag.node(node_id)
        meta_dict = dict(node.meta) if node.meta else {}
        if meta_dict.get("cacheable", False):
            cacheable_nodes.append(node.name)
    
    # Should have multiple cacheable transformations
    assert len(cacheable_nodes) >= 3
    
    # Key transformations should be cacheable
    expected_cacheable = ["noise_filter", "ground_segmentation", "feature_extraction"]
    for cacheable_name in expected_cacheable:
        assert any(cacheable_name in name for name in cacheable_nodes)


def test_coordinate_transform_dag():
    """Test coordinate transformation DAG for geodetic conversions."""
    dag, root, inputs = create_coordinate_transform_dag()
    
    # Validate DAG structure
    assert dag.size() > 0
    assert root in dag._nodes
    
    # Check transformation pipeline stages
    node_names = [dag.node(nid).name for nid in dag._nodes]
    expected_transforms = [
        "wgs84_coordinates", "local_datum_params",
        "ellipsoid_transform", "map_projection", "grid_correction"
    ]
    
    for transform in expected_transforms:
        assert transform in node_names
    
    # Test execution
    plan = build_plan(dag, root, budget_nodes=3)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None
    # Result should be coordinate transformation output
    assert isinstance(result.value, dict)


def test_coordinate_transform_caching():
    """Test coordinate transformation caching for reuse."""
    dag, root, inputs = create_coordinate_transform_dag()
    
    # Check that transformations are marked as cacheable
    cacheable_count = 0
    for node_id in dag._nodes:
        node = dag.node(node_id)
        meta_dict = dict(node.meta) if node.meta else {}
        if meta_dict.get("cacheable", False):
            cacheable_count += 1
    
    # Most coordinate transformations should be cacheable
    assert cacheable_count >= 3


def test_coordinate_transform_priority_classes():
    """Test that coordinate transforms have appropriate priority classes."""
    dag, root, inputs = create_coordinate_transform_dag()
    
    # Check priority class assignments
    p1_nodes = []
    for node_id in dag._nodes:
        node = dag.node(node_id)
        meta_dict = dict(node.meta) if node.meta else {}
        if meta_dict.get("priority_class") == "P1":
            p1_nodes.append(node.name)
    
    # Real-time coordinate transforms should be P1
    assert len(p1_nodes) >= 2


def test_geospatial_demo():
    """Test the complete geospatial demonstration."""
    # This should run without errors
    try:
        demo_point_cloud_pipeline()
    except Exception as e:
        pytest.fail(f"Geospatial demo failed: {e}")


def test_lidar_input_validation():
    """Test LiDAR processing with different input types."""
    dag, root, inputs = create_lidar_processing_dag()
    
    # Test with modified inputs
    modified_inputs = inputs.copy()
    modified_inputs[list(inputs.keys())[0]] = 500000  # Smaller point cloud
    
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, modified_inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_geospatial_memory_efficiency():
    """Test that geospatial processing respects memory constraints."""
    dag, root, inputs = create_lidar_processing_dag()
    
    # Test with very tight memory budget
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_geospatial_deterministic_execution():
    """Test that geospatial processing produces deterministic results."""
    dag, root, inputs = create_lidar_processing_dag()
    
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)
    
    # Run multiple times
    results = []
    for _ in range(3):
        result = evaluator.run(plan)
        results.append(result.value)
    
    # All results should be identical
    assert len(set(results)) == 1


def test_priority_class_distribution():
    """Test priority class distribution across geospatial pipeline."""
    dag, root, inputs = create_lidar_processing_dag()
    
    priority_classes = {}
    for node_id in dag._nodes:
        node = dag.node(node_id)
        meta_dict = dict(node.meta) if node.meta else {}
        priority_class = meta_dict.get("priority_class", "P2")
        priority_classes[priority_class] = priority_classes.get(priority_class, 0) + 1
    
    # Should have appropriate priority distribution
    assert "P2" in priority_classes  # Most operations should be P2
    assert priority_classes["P2"] >= 3