# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Tests for evaluator module.

Tests correct outputs for examples, verify=True path, and recomputation correctness.
"""

import pytest
from collections import OrderedDict
from fractal_down.dag import DAG
from fractal_down.treelift import build_plan, Plan
from fractal_down.evaluator import Evaluator, EvalResult
from fractal_down.examples import make_tiny_dag, make_weighted_dag
import operator


def test_evaluator_creation():
    """Test basic evaluator creation."""
    dag = DAG()
    a = dag.add_leaf("a")

    inputs = {a: 42}
    evaluator = Evaluator(dag, inputs)

    assert evaluator.dag is dag
    assert evaluator.inputs == inputs


def test_invalid_input_nodes():
    """Test error when providing inputs for non-leaf nodes."""
    dag = DAG()
    a = dag.add_leaf("a")
    b = dag.add_op("b", lambda x: x + 1, [a])

    # Try to provide input for operation node
    with pytest.raises(ValueError, match="Input node .* is not a leaf node"):
        Evaluator(dag, {b: 42})


def test_simple_evaluation():
    """Test simple DAG evaluation."""
    dag = DAG()

    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("c", operator.add, [a, b])

    inputs = {a: 5, b: 7}
    plan = Plan(root=c, budget_nodes=3, order=(a, b, c))

    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    assert isinstance(result, EvalResult)
    assert result.value == 12  # 5 + 7
    assert isinstance(result.digest, bytes)


def test_tiny_dag_evaluation():
    """Test evaluation of the tiny example DAG."""
    dag, root, inputs = make_tiny_dag()

    # Build a plan
    plan = build_plan(dag, root, budget_nodes=4)

    # Evaluate
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Expected: (2+3) * (4+5) = 5 * 9 = 45
    assert result.value == 45
    assert isinstance(result.digest, bytes)
    assert len(result.digest) > 0


def test_weighted_dag_evaluation():
    """Test evaluation of weighted DAG."""
    dag, root, inputs = make_weighted_dag()

    plan = build_plan(dag, root, budget_nodes=6)

    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Compute expected result manually
    x1, x2, x3, x4 = inputs[0], inputs[1], inputs[2], inputs[3]
    op1_result = x1 + x2  # 1.5 + 2.5 = 4.0
    op2_result = x3 * x4  # 3.5 * 4.5 = 15.75
    expected = op1_result * op2_result + op1_result - op2_result
    # 4.0 * 15.75 + 4.0 - 15.75 = 63.0 + 4.0 - 15.75 = 51.25

    assert abs(result.value - expected) < 1e-10


def test_recomputation_with_small_budget():
    """Test that small budget works correctly via recomputation."""
    dag = DAG()

    # Create DAG: a, b, c -> add1, add2 -> mul
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_leaf("c")
    add1 = dag.add_op("add1", operator.add, [a, b])
    add2 = dag.add_op("add2", operator.add, [b, c])
    mul = dag.add_op("mul", operator.mul, [add1, add2])

    inputs = {a: 2, b: 3, c: 4}

    # Build plan with tiny budget
    plan = build_plan(dag, mul, budget_nodes=1)

    # Should still work correctly
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Expected: (2+3) * (3+4) = 5 * 7 = 35
    assert result.value == 35


def test_verification_mode():
    """Test verification mode catches inconsistencies."""
    dag, root, inputs = make_tiny_dag()
    plan = build_plan(dag, root, budget_nodes=4)

    evaluator = Evaluator(dag, inputs)

    # Should work fine with verify=True
    result = evaluator.run(plan, verify=True)
    assert result.value == 45

    # Verification should pass (no exception thrown)


def test_missing_input_error():
    """Test error when required input is missing."""
    dag = DAG()
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("c", operator.add, [a, b])

    # Missing input for 'b'
    inputs = {a: 5}
    plan = Plan(root=c, budget_nodes=3, order=(a, b, c))

    evaluator = Evaluator(dag, inputs)
    with pytest.raises(ValueError, match="Missing input value for leaf node"):
        evaluator.run(plan)


def test_digest_consistency():
    """Test that same values produce same digests."""
    dag = DAG()
    a = dag.add_leaf("a")

    inputs = {a: 42}
    plan = Plan(root=a, budget_nodes=1, order=(a,))

    evaluator = Evaluator(dag, inputs)
    result1 = evaluator.run(plan)
    result2 = evaluator.run(plan)

    # Same value should produce same digest
    assert result1.digest == result2.digest


def test_different_values_different_digests():
    """Test that different values produce different digests."""
    dag = DAG()
    a = dag.add_leaf("a")
    plan = Plan(root=a, budget_nodes=1, order=(a,))

    evaluator1 = Evaluator(dag, {a: 42})
    evaluator2 = Evaluator(dag, {a: 43})

    result1 = evaluator1.run(plan)
    result2 = evaluator2.run(plan)

    # Different values should produce different digests
    assert result1.digest != result2.digest


def test_lru_cache_behavior():
    """Test that LRU cache works correctly during evaluation."""
    dag = DAG()

    # Create scenario where LRU matters
    inputs = []
    for i in range(4):
        inputs.append(dag.add_leaf(f"input_{i}"))

    # Operations that reuse inputs
    op1 = dag.add_op("op1", operator.add, [inputs[0], inputs[1]])
    op2 = dag.add_op("op2", operator.add, [inputs[2], inputs[3]])
    op3 = dag.add_op("op3", operator.mul, [inputs[0], op1])  # Reuses input[0]
    final = dag.add_op("final", operator.add, [op2, op3])

    input_values = {inp: i + 1 for i, inp in enumerate(inputs)}
    plan = build_plan(dag, final, budget_nodes=2)

    evaluator = Evaluator(dag, input_values)
    result = evaluator.run(plan)

    # Should compute correctly despite cache evictions
    # op1 = 1 + 2 = 3
    # op2 = 3 + 4 = 7
    # op3 = 1 * 3 = 3
    # final = 7 + 3 = 10
    assert result.value == 10


def test_custom_hash_provider():
    """Test using custom hash provider."""
    from fractal_down.hashing import HashProvider

    class TestHashProvider:
        def digest(self, data: bytes) -> bytes:
            return b"test_hash_" + data[:8]

    dag = DAG()
    a = dag.add_leaf("a")
    inputs = {a: "test"}
    plan = Plan(root=a, budget_nodes=1, order=(a,))

    evaluator = Evaluator(dag, inputs, hash_provider=TestHashProvider())
    result = evaluator.run(plan)

    # Should use custom hash
    assert result.digest.startswith(b"test_hash_")


def test_complex_operations():
    """Test with more complex operations."""
    dag = DAG()

    a = dag.add_leaf("a")
    b = dag.add_leaf("b")

    # Custom operations
    def complex_op(x, y):
        return x**2 + y**2 + x * y

    def sqrt_op(x):
        return x**0.5

    op1 = dag.add_op("complex", complex_op, [a, b])
    op2 = dag.add_op("sqrt", sqrt_op, [op1])

    inputs = {a: 3, b: 4}
    plan = build_plan(dag, op2, budget_nodes=4)

    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Expected: sqrt(3^2 + 4^2 + 3*4) = sqrt(9 + 16 + 12) = sqrt(37)
    expected = (3**2 + 4**2 + 3 * 4) ** 0.5
    assert abs(result.value - expected) < 1e-10


def test_plan_root_mismatch():
    """Test error when plan root doesn't exist in DAG."""
    dag = DAG()
    a = dag.add_leaf("a")

    # Plan with non-existent root
    plan = Plan(root=999, budget_nodes=1, order=(999,))

    evaluator = Evaluator(dag, {a: 1})
    with pytest.raises(ValueError, match="Plan root .* not found in DAG"):
        evaluator.run(plan)


def test_zero_budget():
    """Test behavior with zero budget."""
    dag = DAG()
    a = dag.add_leaf("a")

    inputs = {a: 42}
    plan = Plan(root=a, budget_nodes=0, order=(a,))

    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan)

    # Should still work (recompute everything)
    assert result.value == 42


def test_evaluation_order_independence():
    """Test that different valid execution orders give same result."""
    dag = DAG()

    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_leaf("c")
    add1 = dag.add_op("add1", operator.add, [a, b])
    add2 = dag.add_op("add2", operator.add, [b, c])
    mul = dag.add_op("mul", operator.mul, [add1, add2])

    inputs = {a: 2, b: 3, c: 4}

    # Two different valid orders
    plan1 = Plan(root=mul, budget_nodes=6, order=(a, b, c, add1, add2, mul))
    plan2 = Plan(root=mul, budget_nodes=6, order=(b, a, c, add1, add2, mul))

    evaluator = Evaluator(dag, inputs)
    result1 = evaluator.run(plan1)
    result2 = evaluator.run(plan2)

    # Should give same result
    assert result1.value == result2.value
    assert result1.digest == result2.digest


def test_large_computation():
    """Test with larger computation to check performance."""
    dag = DAG()

    # Create computation tree
    inputs = []
    for i in range(8):
        inputs.append(dag.add_leaf(f"input_{i}"))

    # Build layers of operations
    current = inputs
    while len(current) > 1:
        next_layer = []
        for i in range(0, len(current), 2):
            if i + 1 < len(current):
                op = dag.add_op(
                    f"add_{len(next_layer)}", operator.add, [current[i], current[i + 1]]
                )
                next_layer.append(op)
            else:
                next_layer.append(current[i])
        current = next_layer

    root = current[0]

    input_values = {inp: i + 1 for i, inp in enumerate(inputs)}
    plan = build_plan(dag, root, budget_nodes=4)

    evaluator = Evaluator(dag, input_values)
    result = evaluator.run(plan)

    # Expected: sum of 1+2+...+8 = 36
    assert result.value == sum(range(1, 9))
