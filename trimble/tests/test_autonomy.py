"""
Tests for Trimble autonomy and guidance examples.
"""

import pytest
from trimble.examples.autonomy import (
    create_safety_guidance_dag,
    create_obstacle_detection_dag,
    demo_autonomous_assistance
)
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator


def test_safety_guidance_dag():
    """Test safety-first autonomous guidance DAG."""
    dag, root, inputs = create_safety_guidance_dag()
    
    assert dag.size() > 0
    assert root in dag.nodes()
    
    # Test execution
    plan = build_plan(dag, root, budget_nodes=3)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_obstacle_detection_dag():
    """Test obstacle detection pipeline."""
    dag, root, inputs = create_obstacle_detection_dag()
    
    assert dag.size() > 0
    
    # Test execution
    plan = build_plan(dag, root, budget_nodes=2)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_safety_priority_enforcement():
    """Test that safety operations get absolute priority."""
    dag, root, inputs = create_safety_guidance_dag()
    
    # Check for P0 safety-critical nodes
    p0_nodes = []
    for node_id in dag.nodes():
        node = dag.node(node_id)
        if node.meta.get("priority_class") == "P0":
            p0_nodes.append(node.name)
    
    assert len(p0_nodes) >= 2  # Should have multiple safety-critical operations


def test_latency_critical_identification():
    """Test identification of latency-critical operations."""
    dag, root, inputs = create_safety_guidance_dag()
    
    # Check for latency-critical nodes
    latency_critical = []
    for node_id in dag.nodes():
        node = dag.node(node_id)
        if node.meta.get("latency_critical", False):
            latency_critical.append(node.name)
    
    assert len(latency_critical) >= 1  # Should have latency-critical operations


def test_autonomy_demo():
    """Test autonomous assistance demonstration."""
    try:
        demo_autonomous_assistance()
    except Exception as e:
        pytest.fail(f"Autonomy demo failed: {e}")


def test_deterministic_safety_execution():
    """Test deterministic execution for safety certification."""
    dag, root, inputs = create_safety_guidance_dag()
    
    plan = build_plan(dag, root, budget_nodes=3)
    evaluator = Evaluator(dag, inputs)
    
    # Run multiple times - should be deterministic
    results = []
    for _ in range(2):
        result = evaluator.run(plan)
        results.append(result.value)
    
    # Results should be identical for certification
    assert results[0] == results[1]