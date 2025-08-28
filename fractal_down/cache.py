"""
Plan caching system with fingerprinting and retention for fractal-down.

Provides disk-based caching of execution plans with content-based cache keys
and automatic cleanup of old entries.
"""

import os
import time
from pathlib import Path
from typing import Callable, Optional, Tuple

from fractal_down.dag import DAG
from fractal_down.fractal import FractalParams
from fractal_down.treelift import Plan
from fractal_down.binary_plan import save_plan, load_plan
from fractal_down.hashing import get_default_provider


def get_cache_dir(tenant_id: str = "default") -> Path:
    """Get the plan cache directory for a tenant, creating if necessary."""
    cache_dir_str = os.environ.get("FRACTAL_DOWN_PLANS_DIR")
    if cache_dir_str:
        root_dir = Path(cache_dir_str)
    else:
        root_dir = Path.home() / ".fractal_down" / "plans"

    cache_dir = root_dir / tenant_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_max_keep() -> int:
    """Get maximum number of cached plans to keep."""
    return int(os.environ.get("FRACTAL_DOWN_PLAN_MAX_KEEP", "512"))


def get_or_build_plan(
    dag: DAG,
    root: int,
    budget_nodes: int,
    build_fn: Callable[[], Plan],
    params: Optional[FractalParams] = None,
    *,
    tenant_id: str = "default",
    billing_hook: Optional[Callable[[str, str], None]] = None,
) -> Tuple[Plan, str, bool]:
    """
    Get cached plan or build and cache a new one.

    Args:
        dag: DAG to build plan for
        root: Root node ID
        budget_nodes: Memory budget for plan
        build_fn: Function to build plan if cache miss
        params: Fractal parameters (or None)

    Returns:
        Tuple of (plan, cache_path, was_cached)
        - plan: The execution plan
        - cache_path: Path to cached plan file
        - was_cached: True if loaded from cache, False if newly built
    """
    # Generate cache key fingerprint
    fingerprint = _generate_fingerprint(dag, root, budget_nodes, params)

    # Get cache directory and file path
    cache_dir = get_cache_dir(tenant_id)
    cache_file = cache_dir / f"{fingerprint}.fplan"

    # Try to load from cache
    if cache_file.exists():
        try:
            plan = load_plan(str(cache_file))
            if billing_hook:
                billing_hook(tenant_id, "hit")
            return plan, str(cache_file), True
        except (ValueError, IOError):
            # Cache file corrupted or invalid - remove it
            try:
                cache_file.unlink()
            except OSError:
                pass

    # Cache miss - build new plan
    plan = build_fn()

    # Save to cache
    try:
        save_plan(plan, str(cache_file))
    except IOError:
        # Failed to save - continue without caching
        pass

    # Clean up old cache entries
    _cleanup_cache(cache_dir)

    if billing_hook:
        billing_hook(tenant_id, "miss")

    return plan, str(cache_file), False


def _generate_fingerprint(
    dag: DAG, root: int, budget_nodes: int, params: Optional[FractalParams]
) -> str:
    """
    Generate cache key fingerprint for the given parameters.

    Combines:
    - Canonical DAG description of nodes reachable from root
    - budget_nodes
    - FractalParams (or "None")
    """
    # Get canonical DAG description
    canonical_dag = _canonicalize_dag(dag, root)

    # Add budget
    canonical_str = f"{canonical_dag}|budget={budget_nodes}"

    # Add fractal parameters
    if params is None:
        params_str = "None"
    else:
        params_dict = params.asdict()
        # Sort for determinism
        params_items = sorted(params_dict.items())
        params_str = ",".join(f"{k}={v}" for k, v in params_items)

    canonical_str += f"|params={params_str}"

    # Generate hash of canonical string
    hp = get_default_provider()
    digest = hp.digest(canonical_str.encode("utf-8"))
    return digest.hex()


def _canonicalize_dag(dag: DAG, root: int) -> str:
    """
    Generate canonical string representation of DAG nodes reachable from root.

    Format for each node in postorder:
    "id={id}|name={name}|op={op}|inputs={inputs}|meta={meta}"
    """
    reachable = dag.postorder(root)
    node_strs = []

    for node_id in reachable:
        node = dag.node(node_id)

        # Convert op to string
        if node.op is None:
            op_str = "None"
        else:
            # Try to get qualname, fallback to name, fallback to str
            if hasattr(node.op, "__qualname__"):
                op_str = node.op.__qualname__
            elif hasattr(node.op, "__name__"):
                op_str = node.op.__name__
            else:
                op_str = str(node.op)

        # Format inputs as comma-separated list
        inputs_str = ",".join(map(str, sorted(node.inputs)))

        # Format meta as sorted key=value pairs
        meta_items = []
        for k, v in sorted(node.meta):
            meta_items.append(f"{k}={v}")
        meta_str = ",".join(meta_items)

        # Build node string
        node_str = (
            f"id={node.id}|name={node.name}|op={op_str}|"
            f"inputs={inputs_str}|meta={meta_str}"
        )
        node_strs.append(node_str)

    return "|".join(node_strs)


def _cleanup_cache(cache_dir: Path):
    """Clean up old cache entries, keeping only the newest MAX_KEEP files."""
    max_keep = get_max_keep()

    try:
        # Get all .fplan files with their modification times
        fplan_files = []
        for cache_file in cache_dir.glob("*.fplan"):
            try:
                mtime = cache_file.stat().st_mtime
                fplan_files.append((mtime, cache_file))
            except OSError:
                continue

        # Sort by modification time (newest first)
        fplan_files.sort(key=lambda x: x[0], reverse=True)

        # Remove files beyond the limit
        for _, cache_file in fplan_files[max_keep:]:
            try:
                cache_file.unlink()
            except OSError:
                continue

    except OSError:
        # Failed to clean up cache - continue silently
        pass


def clear_cache():
    """Clear all cached plans for cold performance testing."""
    cache_dir = get_cache_dir()

    try:
        # Remove all .fplan files
        for cache_file in cache_dir.glob("*.fplan"):
            try:
                cache_file.unlink()
            except OSError:
                continue
    except OSError:
        # Failed to clear cache - continue silently
        pass
