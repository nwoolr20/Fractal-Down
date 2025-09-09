# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Tests for Trimble construction and BIM integration examples.
"""

import pytest
from trimble.examples.construction import (
    create_bim_sync_dag,
    create_deviation_detection_dag,
    demo_incremental_bim_sync
)
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams


def test_bim_sync_dag():
    """Test BIM synchronization DAG creation and execution."""
    dag, root, inputs = create_bim_sync_dag()
    
    assert dag.size() > 0
    assert root in dag.nodes()
    assert len(inputs) > 0
    
    # Test execution
    plan = build_plan(dag, root, budget_nodes=3)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_bim_sync_priority_scheduling():
    """Test safety-first priority scheduling in BIM sync."""
    dag, root, inputs = create_bim_sync_dag()
    
    # Check for P0 safety nodes
    safety_nodes = []
    for node_id in dag.nodes():
        node = dag.node(node_id)
        if node.meta.get("priority_class") == "P0":
            safety_nodes.append(node.name)
    
    assert len(safety_nodes) >= 1  # Should have safety-critical processing


def test_deviation_detection_dag():
    """Test as-built vs design deviation detection."""
    dag, root, inputs = create_deviation_detection_dag()
    
    assert dag.size() > 0
    
    # Test execution
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)
    
    assert result.value is not None


def test_construction_demo():
    """Test construction demonstration."""
    try:
        demo_incremental_bim_sync()
    except Exception as e:
        pytest.fail(f"Construction demo failed: {e}")
        

def test_bim_sync_cache_usage():
    """Test that BIM sync uses caching appropriately."""
    dag, root, inputs = create_bim_sync_dag()
    
    cacheable_count = sum(1 for nid in dag.nodes() 
                         if dag.node(nid).meta.get("cacheable", False))
    
    assert cacheable_count >= 2  # Should have cacheable operations