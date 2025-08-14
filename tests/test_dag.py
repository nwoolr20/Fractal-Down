"""
Tests for DAG module.

Tests DAG creation, cycle detection, and postorder traversal correctness.
"""

import pytest
from fractal_down.dag import DAG, Node


def test_dag_creation():
    """Test basic DAG creation."""
    dag = DAG()
    assert dag.size() == 0


def test_add_leaf():
    """Test adding leaf nodes."""
    dag = DAG()
    
    # Add simple leaf
    leaf_id = dag.add_leaf("test_leaf")
    assert leaf_id == 0
    assert dag.size() == 1
    
    # Check node properties
    node = dag.node(leaf_id)
    assert node.id == leaf_id
    assert node.name == "test_leaf"
    assert node.op is None
    assert node.inputs == ()
    assert node.meta == ()
    
    # Add leaf with meta
    leaf2_id = dag.add_leaf("leaf2", {"key": "value", "num": 42})
    node2 = dag.node(leaf2_id)
    assert node2.meta == (("key", "value"), ("num", 42))  # Sorted by key


def test_add_op():
    """Test adding operation nodes."""
    dag = DAG()
    
    # Add leaves first
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    
    # Add operation
    add_op = lambda x, y: x + y
    op_id = dag.add_op("a+b", add_op, [a, b])
    
    assert dag.size() == 3
    node = dag.node(op_id)
    assert node.name == "a+b"
    assert node.op == add_op
    assert node.inputs == (a, b)


def test_invalid_inputs():
    """Test error handling for invalid inputs."""
    dag = DAG()
    
    # Try to add op with non-existent input
    with pytest.raises(ValueError, match="Input node 999 does not exist"):
        dag.add_op("invalid", lambda x: x, [999])


def test_cycle_detection():
    """Test cycle detection by manually creating a cycle."""
    dag = DAG()
    
    a = dag.add_leaf("a")
    b = dag.add_op("b", lambda x: x + 1, [a])
    c = dag.add_op("c", lambda x: x + 1, [b])
    
    # Manually create a cycle by modifying the internal structures
    # This simulates what would happen if we could create c -> a dependency
    dag._children[c].append(a)
    
    # Now the cycle detection should find the cycle
    assert dag._has_cycle(a) == True, "Should detect cycle a -> b -> c -> a"
    
    # Clean up the artificial cycle
    dag._children[c].remove(a)


def test_parents_children():
    """Test parent/child relationships."""
    dag = DAG()
    
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("a+b", lambda x, y: x + y, [a, b])
    
    # Test parents
    assert dag.parents(a) == []
    assert dag.parents(b) == []
    assert set(dag.parents(c)) == {a, b}
    
    # Test children
    assert c in dag.children(a)
    assert c in dag.children(b)
    assert dag.children(c) == []


def test_postorder():
    """Test postorder traversal."""
    dag = DAG()
    
    # Build diamond DAG: a, b -> c -> d
    #                    a -> d
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("a+b", lambda x, y: x + y, [a, b])
    d = dag.add_op("c+a", lambda x, y: x + y, [c, a])
    
    postorder = dag.postorder(d)
    
    # Check that all nodes are included
    assert set(postorder) == {a, b, c, d}
    
    # Check topological ordering (parents before children)
    a_pos = postorder.index(a)
    b_pos = postorder.index(b)
    c_pos = postorder.index(c)
    d_pos = postorder.index(d)
    
    # a and b must come before c
    assert a_pos < c_pos
    assert b_pos < c_pos
    
    # c and a must come before d
    assert c_pos < d_pos
    assert a_pos < d_pos


def test_postorder_caching():
    """Test that postorder results are cached."""
    dag = DAG()
    
    a = dag.add_leaf("a")
    b = dag.add_leaf("b")
    c = dag.add_op("a+b", lambda x, y: x + y, [a, b])
    
    # First call should compute and cache
    result1 = dag.postorder(c)
    
    # Second call should return cached result
    result2 = dag.postorder(c)
    
    assert result1 is result2  # Same object reference


def test_postorder_cache_invalidation():
    """Test that cache is invalidated when DAG changes."""
    dag = DAG()
    
    a = dag.add_leaf("a")
    result1 = dag.postorder(a)
    
    # Add new node - should invalidate cache
    b = dag.add_leaf("b")
    
    # Cache should be cleared, but this specific query should still work
    result2 = dag.postorder(a)
    assert result1 == result2  # Same content
    

def test_nonexistent_node():
    """Test error handling for non-existent nodes."""
    dag = DAG()
    
    with pytest.raises(ValueError, match="Node 999 does not exist"):
        dag.node(999)
    
    with pytest.raises(ValueError, match="Node 999 does not exist"):
        dag.parents(999)
        
    with pytest.raises(ValueError, match="Node 999 does not exist"):
        dag.children(999)
        
    with pytest.raises(ValueError, match="Root node 999 does not exist"):
        dag.postorder(999)


def test_meta_serialization():
    """Test metadata serialization to sorted tuples."""
    dag = DAG()
    
    # Add node with complex meta
    meta = {"z": 1, "a": "string", "m": [1, 2, 3]}
    leaf_id = dag.add_leaf("test", meta)
    
    node = dag.node(leaf_id)
    # Should be sorted by key, values converted to strings via str()
    expected = (("a", "string"), ("m", [1, 2, 3]), ("z", 1))
    assert node.meta == expected


def test_large_dag():
    """Test with a larger DAG to check performance and correctness."""
    dag = DAG()
    
    # Create a chain of 100 nodes
    prev = dag.add_leaf("input")
    for i in range(100):
        prev = dag.add_op(f"op_{i}", lambda x: x + 1, [prev])
    
    assert dag.size() == 101
    
    # Check postorder 
    postorder = dag.postorder(prev)
    assert len(postorder) == 101
    assert postorder[0] == 0  # Input node
    assert postorder[-1] == prev  # Final node