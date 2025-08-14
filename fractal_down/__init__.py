"""
Fractal-Down: Production-grade DAG evaluation with √N memory and fractal priority scheduling.

A dependency-light Python package/CLI that evaluates DAGs using square-root scratch memory
and fractal-down priority scheduling, with binary plan caching and deterministic verification.
"""

from fractal_down.version import __version__
from fractal_down.dag import DAG, Node
from fractal_down.fractal import FractalParams, compute_node_priority
from fractal_down.treelift import Plan, build_plan
from fractal_down.evaluator import Evaluator, EvalResult
from fractal_down.binary_plan import save_plan, load_plan
from fractal_down.cache import get_or_build_plan
from fractal_down.hashing import get_default_provider

__all__ = [
    "__version__",
    "DAG",
    "Node", 
    "FractalParams",
    "compute_node_priority",
    "Plan",
    "build_plan",
    "Evaluator", 
    "EvalResult",
    "save_plan",
    "load_plan",
    "get_or_build_plan",
    "get_default_provider",
]