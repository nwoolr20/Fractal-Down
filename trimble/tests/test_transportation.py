"""Tests for remaining Trimble domain examples."""

import pytest
from trimble.examples.transportation import create_fleet_telematics_dag, demo_logistics_pipeline
from trimble.examples.uav import create_aerial_capture_dag, demo_uav_processing
from trimble.examples.mixed_reality import create_spatial_anchoring_dag, demo_mixed_reality_pipeline
from trimble.examples.digital_twins import create_sensor_fusion_dag, demo_digital_twin_sync
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator


def test_fleet_telematics_dag():
    """Test fleet telematics processing."""
    dag, root, inputs = create_fleet_telematics_dag()
    assert dag.size() > 0
    
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    assert result.value is not None


def test_aerial_capture_dag():
    """Test UAV aerial data capture."""
    dag, root, inputs = create_aerial_capture_dag()
    assert dag.size() > 0
    
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    assert result.value is not None


def test_spatial_anchoring_dag():
    """Test mixed reality spatial anchoring."""
    dag, root, inputs = create_spatial_anchoring_dag()
    assert dag.size() > 0
    
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    assert result.value is not None


def test_sensor_fusion_dag():
    """Test digital twin sensor fusion."""
    dag, root, inputs = create_sensor_fusion_dag()
    assert dag.size() > 0
    
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    assert result.value is not None


def test_transportation_demo():
    """Test transportation demo."""
    try:
        demo_logistics_pipeline()
    except Exception as e:
        pytest.fail(f"Transportation demo failed: {e}")


def test_uav_demo():
    """Test UAV demo."""
    try:
        demo_uav_processing()
    except Exception as e:
        pytest.fail(f"UAV demo failed: {e}")


def test_mixed_reality_demo():
    """Test mixed reality demo."""
    try:
        demo_mixed_reality_pipeline()
    except Exception as e:
        pytest.fail(f"Mixed reality demo failed: {e}")


def test_digital_twin_demo():
    """Test digital twin demo."""
    try:
        demo_digital_twin_sync()
    except Exception as e:
        pytest.fail(f"Digital twin demo failed: {e}")