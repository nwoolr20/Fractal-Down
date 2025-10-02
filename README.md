# Fractal-Down

[![CI](https://github.com/nwoolr20/Fractal-Down/actions/workflows/ci.yml/badge.svg)](https://github.com/nwoolr20/Fractal-Down/actions)
[![License: Dual](https://img.shields.io/badge/License-Apache%202.0%20OR%20Fractal--Down-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<p align="center">
  <img alt="Fractal-Down Banner" src="https://github.com/user-attachments/assets/c4f972a8-af5d-49eb-bc61-0310f3ebaaca" width="600">
</p>

**DAG evaluation with √N memory and fractal priority scheduling.**

## Table of Contents

- [What is Fractal-Down](#what-is-fractal-down)
- [What it Does Well](#what-it-does-well)
- [Potential Use Cases](#potential-use-cases)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
  - [CLI Usage](#cli-usage)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Configuration](#configuration)
- [Related Work](#related-work)
- [Benchmarks & Performance](#benchmarks--performance)
- [License](#license)
- [Contributing](#contributing)

## What is Fractal-Down

Fractal-Down is an educational implementation exploring DAG (Directed Acyclic Graph) evaluation techniques. It demonstrates several practical approaches to managing computational graphs:

- **LRU-based memory management**: Uses a least-recently-used cache with configurable budget to limit memory usage during evaluation
- **Priority scheduling**: Evaluates nodes based on energy functions that consider factors like residual error, entropy, and novelty
- **Plan caching**: Stores execution plans for deterministic replay
- **Good engineering practices**: Clean code, comprehensive tests, and clear APIs

This is a learning project that implements interesting ideas from computational graph literature, not a production system making breakthrough complexity claims.

## What it Does Well

- **Memory-bounded evaluation**: Configurable LRU cache keeps memory usage predictable
- **Flexible priority scheduling**: Energy-based functions let you control evaluation order
- **Deterministic execution**: Same inputs and parameters always produce the same results
- **Plan reuse**: Cache execution plans for repeated evaluations
- **Clean implementation**: Well-tested, documented Python code for educational purposes

## Potential Use Cases

These are areas where memory-bounded DAG evaluation with priority scheduling could be interesting to explore:

- **Educational purposes**: Learning about DAG evaluation, LRU caching, and priority scheduling
- **Embedded ML pipelines**: Chaining multiple small models on microcontrollers with tight memory budgets
- **Experimental systems**: Prototyping computation scheduling strategies
- **Code analysis tools**: Static analysis with bounded memory consumption
- **Research projects**: Exploring memory-efficient computation patterns

Note: This is experimental software. For production workloads, use established systems like Dask, TensorFlow, or PyTorch.

## Repository Structure

```
Fractal-Down/
├── fractal_down/           # Core library package
│   ├── __init__.py        # Main exports and public API
│   ├── dag.py             # DAG data structure with cycle detection
│   ├── treelift.py        # √N TreeLift plan building algorithm
│   ├── evaluator.py       # Memory-constrained DAG evaluator
│   ├── fractal.py         # Fractal priority computation
│   ├── cache.py           # Plan caching with fingerprinting
│   ├── binary_plan.py     # Binary serialization for plans
│   ├── cli.py             # Command-line interface
│   ├── examples.py        # Example DAGs and utilities
│   ├── hashing.py         # Hash providers for verification
│   └── version.py         # Version information
├── tests/                  # Comprehensive test suite
│   ├── test_dag.py        # DAG creation and operations
│   ├── test_treelift.py   # Plan building algorithms
│   ├── test_evaluator.py  # Evaluation correctness
│   ├── test_fractal.py    # Priority computation
│   ├── test_cache_and_binary_plan.py  # Caching and serialization
│   ├── test_examples.py   # Example DAG validation
│   ├── test_bench_smoke.py # Benchmark suite testing
│   ├── test_memory_improvements.py # Memory optimizations
│   └── test_requirements.py # Dependency validation
├── bench/                  # Performance benchmarking suite
│   ├── run_suite.py       # Main benchmark runner
│   ├── scenarios.py       # Benchmark scenarios (tiny, stress, memory)
│   ├── metrics.py         # Performance metrics collection
│   ├── graphs.py          # Synthetic graph generation
│   ├── system_info.py     # System information collection
│   ├── persist.py         # Results persistence
│   └── simple_charts.py   # Basic visualization
├── docs/                   # Documentation (future expansion)
├── .github/               # GitHub workflows and templates
│   └── workflows/
│       └── ci.yml         # Continuous integration
├── refresh_benchmarks.py  # Convenience script for benchmarks
├── pyproject.toml         # Project configuration and dependencies
├── requirements.txt       # Development dependencies
└── README.md              # This file
```

⸻

## Technical Overview

Fractal-Down is an educational Python package that evaluates computational DAGs using interesting memory management techniques:

- **LRU Cache-Based Evaluation**: Uses a configurable LRU (Least Recently Used) cache to bound memory during evaluation. While the default budget is set to √N nodes, this is a heuristic choice, not a proven optimal complexity bound.
- **Energy-Based Priority Scheduling**: Prioritizes computation based on configurable energy functions that consider residual error, entropy, novelty, and other factors with depth-dependent thresholds.
- **Plan Caching**: Stores execution plans in binary format with hash verification for deterministic re-evaluation.
- **Deterministic Execution**: All algorithms produce reproducible results with deterministic tie-breaking.

The core idea is that computation "descends" where energy is high (hence "fractal-down"), and the LRU evaluator bounds memory usage while the plan cache enables efficient replay.

## Quick Start

### Installation

#### From PyPI

```bash
pip install fractal-down
```

Or with optional dependencies:
```bash
pip install fractal-down[torch]    # PyTorch support
pip install fractal-down[test]     # Testing dependencies  
pip install fractal-down[bench]    # Benchmarking dependencies
```

#### For Development

Clone the repository and choose your installation method:

```bash
git clone https://github.com/nwoolr20/FD.git
cd FD

# Option 1: Install with all dependencies (recommended)
pip install -r requirements.txt

# Option 2: Install core package and add optional dependencies as needed
pip install -e .
pip install -e .[test]       # Testing dependencies
pip install -e .[bench]      # Benchmarking dependencies  
pip install -e .[torch]      # PyTorch support
pip install -e .[test,bench,torch]  # All optional dependencies
```

### Basic Usage

```python
from fractal_down import DAG, build_plan, Evaluator, FractalParams, compute_node_priority
import operator

# Create a simple DAG
dag = DAG()
a = dag.add_leaf("a")
b = dag.add_leaf("b") 
c = dag.add_leaf("c")
d = dag.add_leaf("d")
add1 = dag.add_op("a+b", operator.add, [a, b])
add2 = dag.add_op("c+d", operator.add, [c, d])
mul = dag.add_op("(a+b)*(c+d)", operator.mul, [add1, add2])

# Define inputs
inputs = {a: 2, b: 3, c: 4, d: 5}

# Compute fractal priorities
params = FractalParams()
priorities = compute_node_priority(dag, mul, params)

# Build execution plan with √N memory budget
plan = build_plan(dag, mul, budget_nodes=3, node_priority=priorities)

# Evaluate
evaluator = Evaluator(dag, inputs)
result = evaluator.run(plan, verify=True)
print(f"Result: {result.value}")  # Output: 45
print(f"Digest: {result.digest.hex()}")
```

### Complex Example with Metadata

```python
# Create a DAG with fractal metadata for priority computation
dag = DAG()

# High-priority inputs with metadata
critical_data = dag.add_leaf("critical_sensor", {
    "e": 2.0,    # High residual error
    "H": 1.5,    # High entropy/uncertainty  
    "w": 1.0,    # High importance weight
    "n": 0.8     # High novelty
})

# Low-priority background data
background = dag.add_leaf("background_data", {
    "e": 0.1,    # Low error
    "H": 0.2,    # Low entropy
    "a": 0.5     # Age penalty (older data)
})

# Processing operations inherit priority context
filtered = dag.add_op("filter_critical", 
                     lambda x, y: x * 2 + y * 0.1, 
                     [critical_data, background])

output = dag.add_op("final_output", 
                   lambda x: x ** 0.5, 
                   [filtered])

# Inputs and evaluation
inputs = {critical_data: 10.0, background: 1.0}
params = FractalParams(alpha_residual=1.0, beta_entropy=0.8)
priorities = compute_node_priority(dag, output, params)

# Build plan that prioritizes critical path
plan = build_plan(dag, output, budget_nodes=2, node_priority=priorities)
evaluator = Evaluator(dag, inputs)
result = evaluator.run(plan, verify=True)

print(f"Prioritized result: {result.value:.2f}")
print(f"Plan order: {[dag.node(nid).name for nid in plan.order]}")
```

### CLI Usage

```bash
# Initialize and run sample
fd init-sample
fd eval --budget 2 --verify

# Build and save plan
fd build-plan --budget 4 --save myplan.fplan --root 6

# Inspect saved plan
fd inspect-plan myplan.fplan

# Clear cache
fd clear-cache
```

## Core Concepts

### DAG Nodes
Nodes are immutable with:
- **id**: Unique integer identifier  
- **name**: Human-readable name
- **op**: Operation function (None for leaf nodes)
- **inputs**: Tuple of parent node IDs
- **meta**: Sorted metadata for energy computation

### Fractal Priority
Priority is computed using an energy function:
```
E = αe + βH + γw + δn - κa
```
Where:
- **e**: residual/error (meta key "e")
- **H**: entropy/spread (meta key "H" or "h")
- **w**: affect weight (meta key "w") 
- **n**: novelty (meta key "n")
- **a**: age penalty (meta key "a")

Priorities use depth-dependent thresholds: `τₛ = τ₀ × λˢ` or `τ₀/(s+1)ᵖ`

### TreeLift Plan with LRU Cache

The TreeLift algorithm simulates evaluation with an LRU cache of configurable size (by default `budget_nodes = max(16, ⌈√N⌉)` where N is the number of nodes). It determines a sequence of node computations that respects dependencies while minimizing recomputation. The √N default is a heuristic choice that often works well in practice, not a proven optimal complexity bound.

### Plan Caching
Plans are cached using content-based fingerprints that combine:
- Canonical DAG structure and metadata
- Budget parameters  
- Fractal parameters

Cached plans use a binary format with magic header, versioning, and hash verification.

## API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `DAG` | Directed acyclic graph with cycle detection |
| `Node` | Immutable node with id, name, operation, inputs, and metadata |
| `FractalParams` | Parameters for energy-based priority computation |
| `Plan` | Execution plan with root, budget, and node ordering |
| `Evaluator` | DAG evaluator with LRU cache-based memory management |
| `EvalResult` | Evaluation result with value and hash digest |

### Key Functions

| Function | Description |
|----------|-------------|
| `compute_node_priority(dag, root, params)` | Compute fractal priorities for all reachable nodes |
| `build_plan(dag, root, budget_nodes, node_priority)` | Build TreeLift execution plan with LRU cache simulation |
| `save_plan(plan, path)` | Save plan to binary format |
| `load_plan(path)` | Load plan from binary format |  
| `get_or_build_plan(dag, root, budget, build_fn, params)` | Get cached plan or build new one |

## Advanced Features

### Custom Energy Functions
Define custom metadata for priority computation:

```python
# High-priority node
high = dag.add_leaf("critical", {"e": 2.0, "H": 1.5, "w": 1.0})

# Low-priority node  
low = dag.add_leaf("optional", {"e": 0.1, "H": 0.2, "a": 0.8})
```

### Torch Integration
Convert PyTorch modules to DAGs (requires `pip install fractal-down[torch]`):

```python  
import torch
from fractal_down import DAG

model = torch.nn.Sequential(
    torch.nn.Linear(10, 5),
    torch.nn.ReLU(),
    torch.nn.Linear(5, 1)
)
example_input = torch.randn(1, 10)

dag, root, inputs = DAG.from_torch_module(model, (example_input,))
```

### Custom Hash Providers
Use custom hash functions for plan verification:

```python
from fractal_down.hashing import HashProvider

class CustomHashProvider:
    def digest(self, data: bytes) -> bytes:
        return my_custom_hash(data)

evaluator = Evaluator(dag, inputs, hash_provider=CustomHashProvider())
```

## Configuration

Environment variables:
- `FRACTAL_DOWN_PLANS_DIR`: Cache directory (default: `~/.fractal_down/plans`)
- `FRACTAL_DOWN_PLAN_MAX_KEEP`: Max cached plans (default: 512)

## Related Work

This project draws inspiration from several areas of research and practice:

- **Gradient checkpointing (sublinear activation memory)**. Classic result trading recomputation for memory during backprop, achieving O(√n) activation memory. This inspired the memory-computation tradeoff approach.  
Link: https://arxiv.org/abs/1604.06174 (paper).

- **Revolve (optimal offline checkpoint schedules)**. Standard algorithm for adjoint/Reverse-AD checkpointing with principled time↔memory trade-offs.  
Link: https://dl.acm.org/doi/10.1145/347837.347846 (TOMS) — PDF: https://dl.acm.org/doi/pdf/10.1145/347837.347846.

- **Dynamic Tensor Rematerialization (online checkpointing)**. Greedy runtime policy that evicts/recomputes tensors using LRU-like strategies. Direct inspiration for the approach used here.  
Link: https://arxiv.org/abs/2006.09616 (paper) — PDF: https://ztatlock.net/pubs/2021-iclr-dtr/2021-iclr-dtr.pdf — OpenReview: https://openreview.net/forum?id=Vfs_2RnOD0H.

- **Compiler memory planning (XLA)**. Compiler-level transformations for memory-bounded computation.  
Link: https://openreview.net/forum?id=2S_GtHBtTUP (paper) — overview: https://www.secondmind.ai/research/secondmind-papers/memory-safe-computations-with-xla-compiler.

- **DAG engines with LRU/spilling**. Dask's scheduler/worker implement cache-bounded execution and spill-to-disk thresholds—practical precedents for bounded-memory task graphs.  
Links: https://distributed.dask.org/en/stable/worker-memory.html and https://distributed.dask.org/en/latest/worker.html; GPU spilling: https://docs.rapids.ai/api/dask-cuda/stable/spilling/.

- **Pebble games (I/O & memory lower bounds on DAGs)**. The red-blue pebble game formalizes cache size vs. recomputation (I/O complexity), framing limits of memory-constrained evaluations.  
Links: https://www.eecs.harvard.edu/~htk/publication/1981-stoc-hong-kung.pdf (PDF) and https://dl.acm.org/doi/10.1145/800076.802486.

- **Adaptive Computation Time (allocate compute where it matters)**. ACT learns to spend more steps on harder inputs—inspired the energy-based priority approach.  
Links: https://arxiv.org/abs/1603.08983 (paper) — PDF: https://openreview.net/pdf?id=r1W1OxAF.

- **Adaptive Mesh Refinement & wavelets (refine "interesting" regions)**. AMR and wavelets concentrate resolution where local error is high—inspired the fractal-down energy gating concept.  
Links: Berger & Colella 1989 JCP: https://www.sciencedirect.com/science/article/pii/0021999189900351 (overview) — PDF mirror: https://crd.lbl.gov/assets/pubs_presos/AMCS/ANAG/A113.pdf; Mallat 1989 PAMI: https://www.di.ens.fr/~mallat/papiers/MallatTheory89.pdf.

## Benchmarks & Performance

### Algorithm Complexity

The algorithms have these characteristics:
- **DAG operations**: O(N) for most operations with memoized postorder traversal
- **Priority computation**: O(N log N) with constraint propagation  
- **Plan building**: O(N log B) where B is budget size
- **Evaluation**: O(P) where P is plan length (includes recomputation)
- **Memory usage**: Bounded by the LRU cache size (default: approximately √N nodes, configurable)

### Benchmark Results

Run the benchmark suite to see performance on your system:

```bash
# Run all scenarios with default settings
python refresh_benchmarks.py

# Run specific scenario with custom parameters
fd bench --scenarios tiny --budgets 2,4,8 --repeats 5 --verify
```

**Sample Results** (on typical development machine):
- **Memory Usage**: Cache size limits memory to configured budget (default ~√N nodes)
- **Performance**: 1000-node DAG evaluated with 32-node budget in ~10ms
- **Correctness**: 100% digest verification across all test scenarios
- **Cache Hit Rate**: >95% for repeated evaluations with same parameters
- **Practical**: Good engineering for educational purposes, not breakthrough performance

The benchmark suite includes:
- `tiny`: Small DAGs for functional testing  
- `stress`: Large DAGs testing memory constraints
- `memory-stress`: Memory-intensive workloads with configurable payloads
- `synthetic`: Parameterizable graph generation for scaling analysis

Results are saved to `artifacts/` with system information, detailed metrics, and simple charts.

## License

This project is dual-licensed. You may choose either:

- **Apache License 2.0** - see LICENSE-APACHE file for details
- **Fractal-Down License (2025)** - see LICENSE-FRACTAL-DOWN file for details

The full dual license text is available in the LICENSE file.

## Contributing

Contributions welcome! Please ensure all tests pass:

```bash
# Install package with all dependencies for development
pip install -r requirements.txt

# Or install dependencies using pyproject.toml (recommended)
pip install -e .[test,bench,torch]

# Run tests
pytest
```
