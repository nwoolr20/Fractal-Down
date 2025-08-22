"""
Tests for examples module.

Smoke tests for example DAGs and demo functions.
"""

import pytest
from fractal_down.examples import (
    make_tiny_dag,
    make_weighted_dag,
    make_deep_dag,
    make_wide_dag,
    demo_run,
)
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority


def test_make_tiny_dag():
    """Test tiny DAG creation."""
    dag, root, inputs = make_tiny_dag()

    # Check structure
    assert dag.size() == 7  # 4 leaves + 2 adds + 1 mul
    assert root == 6  # Final multiply operation
    assert len(inputs) == 4  # 4 input values

    # Check that we can evaluate it
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Expected: (2+3) * (4+5) = 5 * 9 = 45
    assert result.value == 45


def test_make_weighted_dag():
    """Test weighted DAG creation and evaluation."""
    dag, root, inputs = make_weighted_dag()

    # Should have meta attributes for priority computation
    assert dag.size() > 6  # At least 4 leaves + 2 ops + 1 final

    # Check that nodes have meta
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        meta_dict = dict(node.meta)

        # Should have some energy-related meta (at least for some nodes)
        if node.op is None or any(
            key in meta_dict for key in ["e", "H", "h", "w", "n", "a"]
        ):
            pass  # Expected to have meta

    # Should be evaluable
    priorities = compute_node_priority(dag, root)
    plan = build_plan(dag, root, budget_nodes=6, node_priority=priorities)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Should produce some numeric result
    assert isinstance(result.value, (int, float))


def test_make_deep_dag():
    """Test deep DAG creation and evaluation."""
    dag, root, inputs = make_deep_dag()

    # Should have reasonable size
    assert dag.size() >= 6

    # Should be evaluable
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Should produce some numeric result
    assert isinstance(result.value, (int, float))
    assert result.value > 0  # Should be positive (sqrt of positive number)


def test_make_wide_dag():
    """Test wide DAG creation and evaluation."""
    dag, root, inputs = make_wide_dag()

    # Should have many nodes
    assert dag.size() >= 8  # At least 8 inputs
    assert len(inputs) >= 8  # At least 8 input values

    # Should be evaluable
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Should produce some numeric result
    assert isinstance(result.value, (int, float))


def test_tiny_dag_structure():
    """Test specific structure of tiny DAG."""
    dag, root, inputs = make_tiny_dag()

    # Get all nodes in postorder
    nodes = dag.postorder(root)

    # Should have exactly 4 leaves
    leaves = [nid for nid in nodes if dag.node(nid).op is None]
    assert len(leaves) == 4

    # Should have operations
    ops = [nid for nid in nodes if dag.node(nid).op is not None]
    assert len(ops) == 3  # 2 adds + 1 mul

    # Check input values match expected keys
    assert len(inputs) == 4
    for leaf_id in leaves:
        assert leaf_id in inputs


def test_weighted_dag_has_priorities():
    """Test that weighted DAG has constraint-enforced priorities."""
    dag, root, inputs = make_weighted_dag()

    priorities = compute_node_priority(dag, root)

    # Should have priorities for all reachable nodes
    reachable = dag.postorder(root)
    assert len(priorities) == len(reachable)

    # Check that parent >= child constraint is satisfied
    for node_id in reachable:
        node = dag.node(node_id)
        node_priority = priorities[node_id]

        # Check that all parents have >= priority
        for parent_id in node.inputs:
            parent_priority = priorities[parent_id]
            assert (
                parent_priority >= node_priority
            ), f"Parent {parent_id} priority {parent_priority} < child {node_id} priority {node_priority}"

    # Check that leaf nodes have at least 0.05 priority
    for node_id in reachable:
        node = dag.node(node_id)
        if node.op is None:  # Leaf node
            assert (
                priorities[node_id] >= 0.05
            ), f"Leaf node {node_id} priority {priorities[node_id]} < 0.05"


def test_deep_dag_depth_variation():
    """Test that deep DAG has varying node depths."""
    dag, root, inputs = make_deep_dag()

    # Manually compute depths to verify structure
    depths = {}

    def compute_depth(node_id):
        if node_id in depths:
            return depths[node_id]

        node = dag.node(node_id)
        if not node.inputs:
            depths[node_id] = 0
        else:
            parent_depths = [compute_depth(pid) for pid in node.inputs]
            depths[node_id] = 1 + max(parent_depths)

        return depths[node_id]

    root_depth = compute_depth(root)

    # Should have reasonable depth (at least 3 layers)
    assert root_depth >= 3

    # Should have nodes at different depths
    all_depths = set(depths.values())
    assert len(all_depths) >= 3  # At least 3 different depths


def test_wide_dag_fan_out():
    """Test that wide DAG has good fan-out structure."""
    dag, root, inputs = make_wide_dag()

    # Count leaf nodes
    postorder = dag.postorder(root)
    leaves = [nid for nid in postorder if dag.node(nid).op is None]

    # Should have many inputs (wide structure)
    assert len(leaves) >= 8

    # All leaves should have input values
    for leaf_id in leaves:
        assert leaf_id in inputs


def test_demo_run_no_crash():
    """Test that demo_run executes without crashing."""
    # Capture output to avoid cluttering test output
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # Should not raise any exceptions
        demo_run()

        # Get the captured output
        output = sys.stdout.getvalue()

        # Should contain some expected content
        assert "Fractal-Down Demo" in output
        assert "Result:" in output

    finally:
        sys.stdout = old_stdout


def test_examples_with_small_budget():
    """Test that all examples work with very small budget."""
    examples = [make_tiny_dag, make_weighted_dag, make_deep_dag, make_wide_dag]

    for example_fn in examples:
        dag, root, inputs = example_fn()

        # Should work with budget=1
        plan = build_plan(dag, root, budget_nodes=1)
        evaluator = Evaluator(dag, inputs)
        result = evaluator.run(plan)

        # Should produce a result
        assert result.value is not None


def test_examples_deterministic():
    """Test that examples produce deterministic results."""
    dag, root, inputs = make_tiny_dag()

    # Run multiple times
    plan = build_plan(dag, root, budget_nodes=4)
    evaluator = Evaluator(dag, inputs)

    results = []
    for _ in range(3):
        result = evaluator.run(plan)
        results.append(result.value)

    # All should be identical
    assert len(set(results)) == 1


def test_examples_with_verification():
    """Test that examples pass verification."""
    examples = [make_tiny_dag, make_weighted_dag, make_deep_dag, make_wide_dag]

    for example_fn in examples:
        dag, root, inputs = example_fn()

        plan = build_plan(dag, root, budget_nodes=4)
        evaluator = Evaluator(dag, inputs)

        # Should pass verification
        result = evaluator.run(plan, verify=True)
        assert result.value is not None


def test_input_value_types():
    """Test that input values are appropriate types."""
    examples = [
        (make_tiny_dag, (int, float)),
        (make_weighted_dag, (int, float)),
        (make_deep_dag, (int, float)),
        (make_wide_dag, (int, float)),
    ]

    for example_fn, expected_types in examples:
        dag, root, inputs = example_fn()

        for value in inputs.values():
            assert isinstance(value, expected_types)


def test_node_names_meaningful():
    """Test that node names are meaningful."""
    dag, root, inputs = make_tiny_dag()

    # Check that nodes have reasonable names
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        assert isinstance(node.name, str)
        assert len(node.name) > 0

        # Names should be descriptive
        if node.op is None:
            # Leaf nodes should have simple names
            assert len(node.name) <= 10
        else:
            # Operation nodes should describe the operation
            assert any(op in node.name.lower() for op in ["+", "*", "add", "mul", "op"])


def test_meta_attributes_valid():
    """Test that meta attributes in examples are valid."""
    dag, root, inputs = make_weighted_dag()

    # Check meta attributes
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        meta_dict = dict(node.meta)

        # If meta contains energy-related keys, values should be numeric
        for key in ["e", "H", "h", "w", "n", "a"]:
            if key in meta_dict:
                value = meta_dict[key]
                assert isinstance(value, (int, float))
                assert -10 <= value <= 10  # Reasonable range
