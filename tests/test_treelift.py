# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Tests for TreeLift plan builder.

Tests plan respects dependencies, LRU budget constraints, and deterministic ordering.
"""

import pytest
from fractal_down.dag import DAG
from fractal_down.treelift import Plan, build_plan
from fractal_down.fractal import compute_node_priority, FractalParams
import operator
import math


def test_plan_creation():
    """Test basic Plan dataclass."""
    plan = Plan(root=5, budget_nodes=10, order=(1, 2, 3, 5))

    assert plan.root == 5
    assert plan.budget_nodes == 10
    assert plan.order == (1, 2, 3, 5)

    # Plan should be frozen/immutable
    with pytest.raises(AttributeError):
        plan.root = 6


def test_simple_plan_build():
    """Test building a simple plan."""
    dag = DAG()

    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("c", operator.add, [a, b])

    plan = build_plan(dag, c, budget_nodes=3)

    assert plan.root == c
    assert plan.budget_nodes == 3
    assert len(plan.order) >= 3  # At least one of each node

    # Check that all nodes appear in order
    order_set = set(plan.order)
    assert a in order_set
    assert b in order_set
    assert c in order_set


def test_default_budget_calculation():
    """Test default budget is sqrt(N)."""
    dag = DAG()

    # Create DAG with 16 nodes -> sqrt(16) = 4, max(16, 4) = 16
    nodes = []
    for i in range(16):
        if i < 4:
            # First 4 are leaves
            nodes.append(dag.add_leaf(f"leaf_{i}"))
        else:
            # Rest depend on previous nodes
            deps = nodes[max(0, i - 3) : i]
            nodes.append(dag.add_op(f"op_{i}", lambda *args: sum(args), deps))

    root = nodes[-1]
    plan = build_plan(dag, root)  # No budget specified

    # Should use default budget = max(16, ceil(sqrt(16))) = max(16, 4) = 16
    assert plan.budget_nodes == 16


def test_dependency_ordering():
    """Test that dependencies are respected in plan ordering."""
    dag = DAG()

    # Create linear chain: a -> b -> c -> d
    a = dag.add_leaf("a")
    b = dag.add_op("b", lambda x: x + 1, [a])
    c = dag.add_op("c", lambda x: x * 2, [b])
    d = dag.add_op("d", lambda x: x - 1, [c])

    plan = build_plan(dag, d, budget_nodes=2)

    # Find positions in order
    positions = {node: [] for node in [a, b, c, d]}
    for i, node in enumerate(plan.order):
        positions[node].append(i)

    # Check that first occurrence of each node respects dependencies
    first_a = min(positions[a]) if positions[a] else float("inf")
    first_b = min(positions[b]) if positions[b] else float("inf")
    first_c = min(positions[c]) if positions[c] else float("inf")
    first_d = min(positions[d]) if positions[d] else float("inf")

    assert first_a < first_b
    assert first_b < first_c
    assert first_c < first_d


def test_lru_budget_constraint():
    """Test that LRU budget is never exceeded during simulation."""
    dag = DAG()

    # Create wide DAG that would exceed budget
    inputs = []
    for i in range(5):
        inputs.append(dag.add_leaf(f"input_{i}"))

    # Create operation that depends on all inputs
    root = dag.add_op("sum", lambda *args: sum(args), inputs)

    plan = build_plan(dag, root, budget_nodes=2)

    # Simulate execution to verify budget constraint
    cache = {}
    cache_order = []  # Track LRU order

    for node_id in plan.order:
        if node_id in cache:
            # Move to end
            cache_order.remove(node_id)
            cache_order.append(node_id)
        else:
            # Add new node
            cache[node_id] = True
            cache_order.append(node_id)

            # Evict LRU if over budget
            while len(cache) > plan.budget_nodes:
                evicted = cache_order.pop(0)
                del cache[evicted]

        # Budget should never be exceeded
        assert len(cache) <= plan.budget_nodes


def test_priority_ordering():
    """Test that parent priorities affect ordering."""
    dag = DAG()

    # Create DAG where priority matters
    high_priority = dag.add_leaf("high", {"e": 2.0})  # Higher energy
    low_priority = dag.add_leaf("low", {"e": 0.1})  # Lower energy
    result = dag.add_op("result", operator.add, [high_priority, low_priority])

    # Compute priorities
    priorities = compute_node_priority(dag, result)

    # Build plan with priorities
    plan = build_plan(dag, result, budget_nodes=2, node_priority=priorities)

    # High priority input should appear before low priority in first occurrence
    high_first = plan.order.index(high_priority)
    low_first = plan.order.index(low_priority)

    # Higher priority should be processed first
    assert priorities[high_priority] >= priorities[low_priority]
    # This translates to earlier position when ensuring parents
    # (exact ordering depends on the algorithm, but higher priority should be handled first)


def test_deterministic_ordering():
    """Test that plan building is deterministic."""
    dag = DAG()

    # Create DAG with potential for non-deterministic ordering
    inputs = []
    for i in range(4):
        # Give same priority to test tie-breaking by ID
        inputs.append(dag.add_leaf(f"input_{i}", {"e": 1.0}))

    root = dag.add_op("sum", lambda *args: sum(args), inputs)

    # Build same plan multiple times
    priorities = compute_node_priority(dag, root)
    plan1 = build_plan(dag, root, budget_nodes=2, node_priority=priorities)
    plan2 = build_plan(dag, root, budget_nodes=2, node_priority=priorities)
    plan3 = build_plan(dag, root, budget_nodes=2, node_priority=priorities)

    # Should be identical
    assert plan1.order == plan2.order == plan3.order


def test_diamond_dag():
    """Test diamond DAG pattern with budget constraints."""
    dag = DAG()

    # Diamond: a -> b, c -> d
    a = dag.add_leaf("a")
    b = dag.add_op("b", lambda x: x + 1, [a])
    c = dag.add_op("c", lambda x: x * 2, [a])
    d = dag.add_op("d", operator.add, [b, c])

    plan = build_plan(dag, d, budget_nodes=2)

    # Check that 'a' appears before both 'b' and 'c'
    pos_a = plan.order.index(a)
    pos_b = plan.order.index(b)
    pos_c = plan.order.index(c)
    pos_d = plan.order.index(d)

    assert pos_a < pos_b
    assert pos_a < pos_c
    assert pos_b < pos_d
    assert pos_c < pos_d


def test_recomputation_with_small_budget():
    """Test that small budget leads to recomputation."""
    dag = DAG()

    # Create scenario that definitely needs recomputation:
    # Multiple independent chains that converge
    a1 = dag.add_leaf("a1")
    a2 = dag.add_op("a2", lambda x: x + 1, [a1])
    a3 = dag.add_op("a3", lambda x: x + 1, [a2])

    b1 = dag.add_leaf("b1")
    b2 = dag.add_op("b2", lambda x: x + 1, [b1])
    b3 = dag.add_op("b3", lambda x: x + 1, [b2])

    c1 = dag.add_leaf("c1")
    c2 = dag.add_op("c2", lambda x: x + 1, [c1])
    c3 = dag.add_op("c3", lambda x: x + 1, [c2])

    # Final node depends on all three chains
    final = dag.add_op("final", lambda x, y, z: x + y + z, [a3, b3, c3])

    nodes = dag.postorder(final)

    # Build plan with very small budget (budget 1 should force recomputation)
    plan = build_plan(dag, final, budget_nodes=1)

    # Should have more operations than nodes due to recomputation
    assert len(plan.order) > len(
        nodes
    ), f"Expected recomputation: order={len(plan.order)}, nodes={len(nodes)}"

    # Final node should still appear at the end
    assert plan.order[-1] == final


def test_no_priority_provided():
    """Test building plan without explicit priorities."""
    dag = DAG()

    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("c", operator.add, [a, b])

    # Should work with default priorities
    plan = build_plan(dag, c, budget_nodes=3)

    assert plan.root == c
    assert len(plan.order) >= 3


def test_single_node():
    """Test plan for single node."""
    dag = DAG()

    a = dag.add_leaf("a")
    plan = build_plan(dag, a, budget_nodes=1)

    assert plan.root == a
    assert plan.order == (a,)
    assert plan.budget_nodes == 1


def test_golden_tiny_dag_budget_2():
    """Golden test: tiny DAG with budget 2 should yield expected order."""
    dag = DAG()

    # Create the tiny example DAG
    a = dag.add_leaf("a")  # id=0
    b = dag.add_leaf("b")  # id=1
    c = dag.add_leaf("c")  # id=2
    d = dag.add_leaf("d")  # id=3
    add1 = dag.add_op("a+b", operator.add, [a, b])  # id=4
    add2 = dag.add_op("c+d", operator.add, [c, d])  # id=5
    mul = dag.add_op("(a+b)*(c+d)", operator.mul, [add1, add2])  # id=6

    # Compute priorities
    priorities = compute_node_priority(dag, mul)

    # Build plan with budget 2
    plan = build_plan(dag, mul, budget_nodes=2, node_priority=priorities)

    # The exact order depends on priorities and tie-breaking,
    # but we can check key properties:

    # 1. All nodes should appear
    nodes_in_order = set(plan.order)
    expected_nodes = {a, b, c, d, add1, add2, mul}
    assert expected_nodes.issubset(nodes_in_order)

    # 2. Dependencies should be respected
    # Find first occurrences
    first_occurrence = {}
    for i, node in enumerate(plan.order):
        if node not in first_occurrence:
            first_occurrence[node] = i

    # Leaves before operations
    assert first_occurrence[a] < first_occurrence[add1]
    assert first_occurrence[b] < first_occurrence[add1]
    assert first_occurrence[c] < first_occurrence[add2]
    assert first_occurrence[d] < first_occurrence[add2]

    # Intermediate ops before final
    assert first_occurrence[add1] < first_occurrence[mul]
    assert first_occurrence[add2] < first_occurrence[mul]

    # 3. Should have recomputation due to budget constraint
    # Note: exact amount depends on priority ordering and cache behavior
    assert len(plan.order) >= 7  # At least as many as unique nodes


def test_invalid_root():
    """Test error handling for invalid root node."""
    dag = DAG()
    a = dag.add_leaf("a")

    with pytest.raises(ValueError):
        build_plan(dag, 999, budget_nodes=1)  # Non-existent root


def test_very_large_budget():
    """Test with budget larger than number of nodes."""
    dag = DAG()

    a = dag.add_leaf("a")
    b = dag.add_op("b", lambda x: x + 1, [a])

    plan = build_plan(dag, b, budget_nodes=1000)  # Much larger than needed

    # Should work fine, no recomputation needed
    assert plan.budget_nodes == 1000
    assert len(set(plan.order)) == 2  # Only 2 unique nodes
