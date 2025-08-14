"""
Tests for fractal priority computation.

Tests energy math, thresholds, parent≥child priority constraint, and determinism.
"""

import pytest
from fractal_down.dag import DAG
from fractal_down.fractal import FractalParams, compute_node_priority
import operator


def test_fractal_params_defaults():
    """Test default fractal parameters."""
    params = FractalParams()
    assert params.alpha == 1.0
    assert params.beta == 0.6
    assert params.gamma == 0.8
    assert params.delta == 0.5
    assert params.kappa == 0.4
    assert params.tau0 == 0.25
    assert params.lambda_ == 0.7
    assert params.p is None


def test_fractal_params_asdict():
    """Test parameter serialization."""
    params = FractalParams(alpha=2.0, beta=0.5)
    d = params.asdict()
    assert d['alpha'] == 2.0
    assert d['beta'] == 0.5
    assert 'lambda_' in d


def test_simple_priority_computation():
    """Test basic priority computation."""
    dag = DAG()
    
    # Create simple DAG with meta
    a = dag.add_leaf("a", {"e": 1.0, "H": 0.5})
    b = dag.add_leaf("b", {"e": 0.5, "H": 1.0})
    c = dag.add_op("a+b", operator.add, [a, b], {"e": 0.8, "H": 0.8})
    
    priorities = compute_node_priority(dag, c)
    
    # Should have priorities for all reachable nodes
    assert set(priorities.keys()) == {a, b, c}
    
    # All priorities should be in [0, 1]
    for p in priorities.values():
        assert 0.0 <= p <= 1.0
    
    # Inputs should have minimum priority of 0.05
    assert priorities[a] >= 0.05
    assert priorities[b] >= 0.05


def test_energy_computation():
    """Test energy function computation."""
    dag = DAG()
    
    # Test with specific meta values
    # E = αe + βH + γw + δn - κa
    # With defaults: E = 1.0*e + 0.6*H + 0.8*w + 0.5*n - 0.4*a
    meta = {"e": 2.0, "H": 1.0, "w": 1.5, "n": 1.0, "a": 0.5}
    a = dag.add_leaf("a", meta)
    
    priorities = compute_node_priority(dag, a)
    
    # Expected energy: 2.0 + 0.6 + 1.2 + 0.5 - 0.2 = 4.1
    # At depth 0, threshold is tau0 = 0.25
    # Raw score = max(0, 4.1 - 0.25) = 3.85
    # Since it's the only node, normalized score is 1.0
    # Plus input minimum 0.05, so max(1.0, 0.05) = 1.0
    assert priorities[a] == 1.0


def test_depth_dependent_thresholds():
    """Test that thresholds depend on node depth."""
    dag = DAG()
    
    # Create chain with same energy at different depths
    meta = {"e": 1.0}
    a = dag.add_leaf("a", meta)  # depth 0
    b = dag.add_op("b", lambda x: x, [a], meta)  # depth 1
    c = dag.add_op("c", lambda x: x, [b], meta)  # depth 2
    
    params = FractalParams(lambda_=0.5)  # Threshold halves each depth
    priorities = compute_node_priority(dag, c, params)
    
    # Higher depth should have lower threshold, so higher priority
    # (assuming energy is above all thresholds)
    assert priorities[c] >= priorities[b] >= priorities[a]


def test_power_law_thresholds():
    """Test power law threshold calculation."""
    dag = DAG()
    
    meta = {"e": 1.0}
    a = dag.add_leaf("a", meta)
    b = dag.add_op("b", lambda x: x, [a], meta)
    
    # Use power law: tau = tau0 / (s+1)^p
    params = FractalParams(p=0.5, tau0=1.0)
    priorities = compute_node_priority(dag, b, params)
    
    # Depth 0: tau = 1.0 / 1^0.5 = 1.0
    # Depth 1: tau = 1.0 / 2^0.5 = 1.0 / 1.414... ≈ 0.707
    # Since energy is 1.0, both should have positive raw scores
    # But different thresholds will affect relative priorities
    assert all(p > 0 for p in priorities.values())


def test_parent_child_constraint():
    """Test that parent priority >= child priority."""
    dag = DAG()
    
    # Create DAG where child would naturally have higher priority
    # Parent has low energy, child has high energy
    parent = dag.add_leaf("parent", {"e": 0.1})  
    child = dag.add_op("child", lambda x: x, [parent], {"e": 2.0})
    
    priorities = compute_node_priority(dag, child)
    
    # Constraint should ensure parent >= child
    assert priorities[parent] >= priorities[child]


def test_input_minimum_priority():
    """Test that input nodes get minimum priority of 0.05."""
    dag = DAG()
    
    # Create input with very low energy (should result in 0 priority)
    a = dag.add_leaf("a", {"e": -10.0})  # Very negative energy
    
    priorities = compute_node_priority(dag, a)
    
    # Should still get minimum 0.05
    assert priorities[a] >= 0.05


def test_deterministic_computation():
    """Test that priority computation is deterministic."""
    dag = DAG()
    
    # Create DAG with multiple nodes
    a = dag.add_leaf("a", {"e": 0.5, "H": 0.3})
    b = dag.add_leaf("b", {"e": 0.7, "H": 0.2})  
    c = dag.add_op("c", operator.add, [a, b], {"e": 0.6, "H": 0.4})
    d = dag.add_op("d", operator.mul, [b, c], {"e": 0.8, "H": 0.1})
    
    # Compute multiple times
    params = FractalParams()
    priorities1 = compute_node_priority(dag, d, params)
    priorities2 = compute_node_priority(dag, d, params)
    priorities3 = compute_node_priority(dag, d, params)
    
    # Should be identical
    assert priorities1 == priorities2 == priorities3


def test_zero_energy_handling():
    """Test handling of zero energy values."""
    dag = DAG()
    
    # All nodes with zero energy
    a = dag.add_leaf("a")  # No meta = all zeros
    b = dag.add_leaf("b", {})  # Empty meta = all zeros
    c = dag.add_op("c", operator.add, [a, b])
    
    priorities = compute_node_priority(dag, c)
    
    # Should still have valid priorities
    assert all(0.0 <= p <= 1.0 for p in priorities.values())
    # Inputs should still get minimum
    assert priorities[a] >= 0.05
    assert priorities[b] >= 0.05


def test_meta_key_variations():
    """Test that both 'H' and 'h' work for entropy."""
    dag = DAG()
    
    a = dag.add_leaf("a", {"e": 1.0, "H": 0.5})
    b = dag.add_leaf("b", {"e": 1.0, "h": 0.5})  # lowercase h
    
    priorities_a = compute_node_priority(dag, a)
    priorities_b = compute_node_priority(dag, b)
    
    # Should give same result
    assert priorities_a[a] == priorities_b[b]


def test_complex_constraint_propagation():
    """Test constraint propagation in complex DAG."""
    dag = DAG()
    
    # Create diamond pattern
    a = dag.add_leaf("a", {"e": 0.1})
    b = dag.add_leaf("b", {"e": 0.1})  
    c = dag.add_op("c", operator.add, [a, b], {"e": 2.0})  # High energy
    d = dag.add_op("d", operator.mul, [a, c], {"e": 0.1})  # Low energy
    
    priorities = compute_node_priority(dag, d)
    
    # Check all constraints
    assert priorities[a] >= priorities[c]  # Parent >= child
    assert priorities[a] >= priorities[d]  # Parent >= child
    assert priorities[b] >= priorities[c]  # Parent >= child
    assert priorities[c] >= priorities[d]  # Parent >= child


def test_no_params():
    """Test with None parameters (should use defaults)."""
    dag = DAG()
    
    a = dag.add_leaf("a", {"e": 1.0})
    b = dag.add_op("b", lambda x: x, [a], {"e": 0.5})
    
    priorities = compute_node_priority(dag, b, None)
    
    assert len(priorities) == 2
    assert all(0.0 <= p <= 1.0 for p in priorities.values())


def test_large_priority_differences():
    """Test handling of very large priority differences."""
    dag = DAG()
    
    # Create nodes with extreme energy differences
    low = dag.add_leaf("low", {"e": -100.0})
    high = dag.add_leaf("high", {"e": 100.0})
    
    priorities_low = compute_node_priority(dag, low)
    priorities_high = compute_node_priority(dag, high)
    
    # Both should still be in valid range
    assert 0.0 <= priorities_low[low] <= 1.0
    assert 0.0 <= priorities_high[high] <= 1.0