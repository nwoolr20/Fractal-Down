"""
Example DAGs for fractal-down demonstration and testing.

Provides sample computational graphs for quickstart and testing purposes.
"""

from typing import Dict, List, Tuple, Any
import operator

from fractal_down.dag import DAG


def make_tiny_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a tiny sample DAG for testing and demonstration.

    Structure:
    - 4 leaf nodes (a, b, c, d)
    - 2 add operations (a+b, c+d)
    - 1 multiply operation ((a+b) * (c+d))

    Returns:
        Tuple of (DAG, root_id, input_values)
    """
    dag = DAG()

    # Add leaf nodes
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_leaf("c")
    d = dag.add_leaf("d")

    # Add operations
    add1 = dag.add_op("a+b", operator.add, [a, b])
    add2 = dag.add_op("c+d", operator.add, [c, d])
    mul = dag.add_op("(a+b)*(c+d)", operator.mul, [add1, add2])

    # Input values
    inputs = {a: 2, b: 3, c: 4, d: 5}

    return dag, mul, inputs


def make_weighted_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a weighted DAG with meta attributes for fractal priority demonstration.

    Shows how different energy components (e, H, w, n, a) affect priority computation.

    Returns:
        Tuple of (DAG, root_id, input_values)
    """
    dag = DAG()

    # Add leaf nodes with varying meta attributes
    x1 = dag.add_leaf("x1", {"e": 0.8, "H": 0.3, "w": 0.5, "n": 0.9, "a": 0.1})
    x2 = dag.add_leaf("x2", {"e": 0.2, "H": 0.7, "w": 0.8, "n": 0.4, "a": 0.3})
    x3 = dag.add_leaf("x3", {"e": 0.5, "H": 0.9, "w": 0.2, "n": 0.7, "a": 0.5})
    x4 = dag.add_leaf("x4", {"e": 0.1, "H": 0.1, "w": 0.1, "n": 0.1, "a": 0.9})

    # Add intermediate operations with meta
    op1 = dag.add_op(
        "x1+x2",
        operator.add,
        [x1, x2],
        {"e": 0.6, "H": 0.4, "w": 0.7, "n": 0.5, "a": 0.2},
    )
    op2 = dag.add_op(
        "x3*x4",
        operator.mul,
        [x3, x4],
        {"e": 0.9, "H": 0.8, "w": 0.3, "n": 0.8, "a": 0.4},
    )

    # Final operation
    root = dag.add_op(
        "final",
        lambda a, b: a * b + a - b,
        [op1, op2],
        {"e": 0.7, "H": 0.6, "w": 0.9, "n": 0.6, "a": 0.3},
    )

    # Input values
    inputs = {x1: 1.5, x2: 2.5, x3: 3.5, x4: 4.5}

    return dag, root, inputs


def make_deep_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a deeper DAG to test depth-based threshold scaling.

    Structure: Linear chain with some branching to test depth computation.

    Returns:
        Tuple of (DAG, root_id, input_values)
    """
    dag = DAG()

    # Base inputs
    x = dag.add_leaf("x", {"e": 1.0})
    y = dag.add_leaf("y", {"e": 0.8})
    z = dag.add_leaf("z", {"e": 0.6})

    # Layer 1
    op1 = dag.add_op("x+1", lambda x: x + 1, [x], {"e": 0.9, "H": 0.2})
    op2 = dag.add_op("y*2", lambda y: y * 2, [y], {"e": 0.7, "H": 0.4})

    # Layer 2
    op3 = dag.add_op("op1+op2", operator.add, [op1, op2], {"e": 0.8, "H": 0.5})
    op4 = dag.add_op("z+op1", operator.add, [z, op1], {"e": 0.6, "H": 0.3})

    # Layer 3
    op5 = dag.add_op("op3*op4", operator.mul, [op3, op4], {"e": 0.5, "H": 0.6})

    # Layer 4
    root = dag.add_op("sqrt", lambda x: x**0.5, [op5], {"e": 0.4, "H": 0.7})

    inputs = {x: 10, y: 5, z: 2}

    return dag, root, inputs


def make_wide_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create a wide DAG with many inputs converging to test budget constraints.

    Returns:
        Tuple of (DAG, root_id, input_values)
    """
    dag = DAG()

    # Create many input nodes
    num_inputs = 8
    inputs = {}
    input_ids = []

    for i in range(num_inputs):
        meta = {"e": 0.1 * (i + 1), "H": 0.05 * i, "w": 0.2, "n": 0.1, "a": 0.05 * i}
        input_id = dag.add_leaf(f"input_{i}", meta)
        input_ids.append(input_id)
        inputs[input_id] = float(i + 1)

    # Pairwise operations
    pair_ops = []
    for i in range(0, len(input_ids), 2):
        if i + 1 < len(input_ids):
            op_id = dag.add_op(
                f"pair_{i//2}",
                operator.add,
                [input_ids[i], input_ids[i + 1]],
                {"e": 0.3, "H": 0.4, "w": 0.5},
            )
            pair_ops.append(op_id)
        else:
            # Odd number - add single node
            pair_ops.append(input_ids[i])

    # Combine pairs
    while len(pair_ops) > 1:
        next_level = []
        for i in range(0, len(pair_ops), 2):
            if i + 1 < len(pair_ops):
                op_id = dag.add_op(
                    f"combine_{len(next_level)}",
                    operator.mul,
                    [pair_ops[i], pair_ops[i + 1]],
                    {"e": 0.6, "H": 0.7, "w": 0.8},
                )
                next_level.append(op_id)
            else:
                next_level.append(pair_ops[i])
        pair_ops = next_level

    root = pair_ops[0]

    return dag, root, inputs


def demo_run():
    """
    Quick demonstration function showing basic fractal-down usage.

    Creates a tiny DAG, builds a plan, and evaluates it.
    """
    from fractal_down.treelift import build_plan
    from fractal_down.evaluator import Evaluator
    from fractal_down.fractal import compute_node_priority, FractalParams

    print("=== Fractal-Down Demo ===")

    # Create sample DAG
    dag, root, inputs = make_tiny_dag()
    print(f"Created DAG with {dag.size()} nodes, root={root}")

    # Show the structure
    print("\nDAG structure:")
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        if node.op is None:
            print(f"  {node_id}: {node.name} (leaf)")
        else:
            print(f"  {node_id}: {node.name} = {node.op.__name__}({list(node.inputs)})")

    # Compute priorities
    params = FractalParams()
    priorities = compute_node_priority(dag, root, params)
    print(f"\nNode priorities: {priorities}")

    # Build plan
    plan = build_plan(dag, root, budget_nodes=2, node_priority=priorities)
    print(f"\nPlan with budget=2:")
    print(f"  Order: {plan.order}")
    print(f"  Length: {len(plan.order)}")

    # Evaluate
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=True)
    print(f"\nResult: {result.value}")
    print(f"Digest: {result.digest.hex()}")

    # Expected result: (2+3) * (4+5) = 5 * 9 = 45
    print(f"Expected: {(inputs[0] + inputs[1]) * (inputs[2] + inputs[3])}")


if __name__ == "__main__":
    demo_run()
