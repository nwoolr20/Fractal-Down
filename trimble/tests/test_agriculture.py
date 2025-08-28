"""
Tests for Trimble precision agriculture examples.
"""

import pytest
from trimble.examples.agriculture import (
    create_precision_agriculture_dag,
    create_multi_machine_coordination_dag,
    demo_field_processing_pipeline
)
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator


def test_precision_agriculture_dag():
    """Test precision agriculture DAG creation and execution."""
    dag, root, inputs = create_precision_agriculture_dag()
    
    assert dag.size() > 0
    assert root in dag.nodes()
    
    # Test execution with edge memory constraints
    plan = build_plan(dag, root, budget_nodes=3)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None
    assert result.peak_memory_nodes <= 3


def test_agriculture_fallback_behavior():
    """Test graceful degradation when ML models unavailable."""
    dag, root, inputs = create_precision_agriculture_dag()
    
    # Check for fallback-enabled nodes
    fallback_nodes = []
    for node_id in dag.nodes():
        node = dag.node(node_id)
        if node.meta.get("fallback_available", False):
            fallback_nodes.append(node.name)
    
    assert len(fallback_nodes) >= 1  # Should have fallback capability


def test_multi_machine_coordination_dag():
    """Test multi-machine coordination with weather priorities."""
    dag, root, inputs = create_multi_machine_coordination_dag()
    
    assert dag.size() > 0
    
    # Test execution
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_agriculture_demo():
    """Test agriculture demonstration."""
    try:
        demo_field_processing_pipeline()
    except Exception as e:
        pytest.fail(f"Agriculture demo failed: {e}")


def test_weather_sensitive_prioritization():
    """Test weather-sensitive operation prioritization."""
    dag, root, inputs = create_multi_machine_coordination_dag()
    
    # Check for P0 weather-sensitive nodes
    p0_nodes = []
    for node_id in dag.nodes():
        node = dag.node(node_id)
        if node.meta.get("priority_class") == "P0":
            p0_nodes.append(node.name)
    
    assert len(p0_nodes) >= 1  # Should have weather-critical operations