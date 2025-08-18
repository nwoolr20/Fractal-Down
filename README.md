# Fractal-Down

Production-grade DAG evaluation with √N memory and fractal priority scheduling.

## Why Fractal-Down

Fractal-Down lets me run big, dependency-heavy graphs on small machines—fast enough, memory-safe, and reproducible—by spending compute only where the signal is. I bound peak scratch to ≈√N nodes, schedule high-value paths first, and cache the execution plan (not activations) for deterministic replay later.

## What it buys me

- **Bounded RAM by design**. Peak scratch scales ≈ √N instead of N, so 8–16 GB laptops/phones can handle graphs that normally need workstations.
- **Anytime results**. I can stop early and still have a coherent answer; more time just refines "interesting" parts.
- **Deterministic replay**. Binary plans cache the execution recipe; I can reproduce the exact result later/on another box.
- **Lower energy & cost**. Recompute beats hoarding memory—great for edge, mobile, and cost-sensitive servers.

## Where I use it (real-world)

- **On-device AI / edge inference**: retrieval, ranking, feature pipelines under hard memory ceilings.
- **Search/RAG pipelines**: pre-plan a query DAG; descend only into shards with high residual/novelty; cache the plan for popular queries.
- **Code intelligence on huge repos**: static analysis/refs with √N scratch; stream early results, get full fidelity if I let it run.
- **Security scanning**: CVE/secret scans with priority on recent/high-risk code; stay inside CI memory quotas.
- **Data engineering on small boxes**: transforms/joins over "too big" datasets via planning + spill + recompute.
- **Scientific/geo**: tiles/LiDAR/PDE-ish graphs—refine where error spikes, not the whole surface.
- **Vision/video analytics**: push depth into salient regions (motion/faces/text), keep backgrounds coarse—fits tight VRAM.
- **Robotics & SLAM**: bounded map updates on embedded hardware; refine high-uncertainty nodes only.
- **Finance/backtesting**: signals → features → strategies; drill into high-residual regimes; plans aid audit.
- **Genomics/bio**: large variant/annotation DAGs under strict RAM; reuse plan recipes across cohorts.

## Two quick scenarios

1. **RAG on a 12 GB laptop**. Baseline O(N) memory trips on large corpora. Fractal-Down sets a √N cache (e.g., 256 nodes), evaluates high-salience shards first, spills/recomputes the rest. I get usable answers immediately; full fidelity if I let it finish. Next identical query replays instantly from the cached plan.

2. **CI security scan with a 4 GB cap**. Parse → tokenize → rules → report. With √N scratch and priority on "recent/critical" code, the job stays within memory limits and finishes predictably instead of failing or thrashing. Plans make recurring scans faster.

## Who benefits

Data/ML engineers, product teams, SRE/platform, researchers, and robotics/embedded—anyone who needs strict memory envelopes without giving up correctness.

**Bottom line**: I turn memory into a safe constant—even on small devices—while steering compute where it matters most, and I make those choices portable and repeatable via cached plan recipes.

⸻

## Technical Overview

Fractal-Down is a Python package that evaluates computational DAGs (Directed Acyclic Graphs) using innovative memory-efficient algorithms:

- **√N Memory Complexity**: Uses square-root of graph size for scratch memory, making it feasible to evaluate large graphs on memory-constrained systems
- **Fractal Priority Scheduling**: Prioritizes computation based on energy functions that consider residual error, entropy, novelty, and other factors with depth-dependent thresholds
- **Plan Caching**: Stores execution plans in binary format with hash verification for fast re-evaluation
- **Deterministic**: All algorithms produce reproducible results with deterministic tie-breaking

The core idea is that computation "descends" only where energy is high (hence "fractal-down"), and the √N evaluator bounds scratch memory usage while the plan cache saves recipes rather than activations.

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

### √N TreeLift Plan
The TreeLift algorithm simulates evaluation with an LRU cache of size `budget_nodes = max(16, ⌈√N⌉)` where N is the number of nodes. It determines the optimal sequence of node computations that respects dependencies while minimizing recomputation.

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
| `Evaluator` | DAG evaluator with √N memory constraint |
| `EvalResult` | Evaluation result with value and hash digest |

### Key Functions

| Function | Description |
|----------|-------------|
| `compute_node_priority(dag, root, params)` | Compute fractal priorities for all reachable nodes |
| `build_plan(dag, root, budget_nodes, node_priority)` | Build √N TreeLift execution plan |
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

- **Square-root–space simulation (complexity theory)**. Williams shows any time-t multitape TM can be simulated in O(√(t log t)) space, implying bounded-fan-in circuits of size s can be evaluated in Õ(√s) space—the theoretical backbone for √-space runtimes.  
Link: https://arxiv.org/abs/2502.17779 (paper) and https://people.csail.mit.edu/rrw/time-vs-space.pdf (PDF).

- **Gradient checkpointing (sublinear activation memory)**. Classic result trading recomputation for memory during backprop, achieving O(√n) activation memory.  
Link: https://arxiv.org/abs/1604.06174 (paper).

- **Revolve (optimal offline checkpoint schedules)**. Standard algorithm for adjoint/Reverse-AD checkpointing with principled time↔memory trade-offs.  
Link: https://dl.acm.org/doi/10.1145/347837.347846 (TOMS) — PDF: https://dl.acm.org/doi/pdf/10.1145/347837.347846.

- **Dynamic Tensor Rematerialization (online checkpointing)**. Greedy runtime policy that evicts/recomputes tensors; proves Ω(√N)-memory training for simple models; works with dynamic graphs.  
Link: https://arxiv.org/abs/2006.09616 (paper) — PDF: https://ztatlock.net/pubs/2021-iclr-dtr/2021-iclr-dtr.pdf — OpenReview: https://openreview.net/forum?id=Vfs_2RnOD0H.

- **Compiler memory planning (XLA)**. Compiler-level transformations that reshape compute to fit explicit memory limits ("memory-safe computations"), complementary to runtime policies.  
Link: https://openreview.net/forum?id=2S_GtHBtTUP (paper) — overview: https://www.secondmind.ai/research/secondmind-papers/memory-safe-computations-with-xla-compiler.

- **DAG engines with LRU/spilling**. Dask's scheduler/worker implement cache-bounded execution and spill-to-disk thresholds—practical precedents for bounded-memory task graphs (not targeting √N or fractal priority).  
Links: https://distributed.dask.org/en/stable/worker-memory.html and https://distributed.dask.org/en/latest/worker.html; GPU spilling: https://docs.rapids.ai/api/dask-cuda/stable/spilling/.

- **Pebble games (I/O & memory lower bounds on DAGs)**. The red-blue pebble game formalizes cache size vs. recomputation (I/O complexity), framing limits of memory-constrained evaluations.  
Links: https://www.eecs.harvard.edu/~htk/publication/1981-stoc-hong-kung.pdf (PDF) and https://dl.acm.org/doi/10.1145/800076.802486.

- **Adaptive Computation Time (allocate compute where it matters)**. ACT learns to spend more steps on harder inputs—an architectural analogue of salience-gated descent.  
Links: https://arxiv.org/abs/1603.08983 (paper) — PDF: https://openreview.net/pdf?id=r1W1OxAF.

- **Adaptive Mesh Refinement & wavelets (refine "interesting" regions)**. AMR and wavelets concentrate resolution where local error is high—classical inspiration for fractal-down gating.  
Links: Berger & Colella 1989 JCP: https://www.sciencedirect.com/science/article/pii/0021999189900351 (overview) — PDF mirror: https://crd.lbl.gov/assets/pubs_presos/AMCS/ANAG/A113.pdf; Mallat 1989 PAMI: https://www.di.ens.fr/~mallat/papiers/MallatTheory89.pdf.

- **Tree Evaluation in near-log space (enabler for Williams)**. Cook & Mertz give a space-efficient algorithm for Tree Evaluation used inside the √-space time simulation.  
Links: https://dl.acm.org/doi/10.1145/3618260.3649664 (STOC '24) — PDF: https://iuuk.mff.cuni.cz/~iwmertz/papers/cm24.tree_evaluation_is_in_space_lognloglogn.pdf.

## Performance

The algorithms are designed for efficiency:
- **DAG operations**: O(N) for most operations with memoized postorder traversal
- **Priority computation**: O(N log N) with constraint propagation  
- **Plan building**: O(N log B) where B is budget size
- **Evaluation**: O(P) where P is plan length (includes recomputation)
- **Memory usage**: O(√N) scratch space during evaluation

## License

MIT License - see LICENSE file for details.

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