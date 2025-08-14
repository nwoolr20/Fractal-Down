# Fractal-Down

Why Fractal-Down

Fractal-Down lets me run big, dependency-heavy graphs on small machines—fast enough, memory-safe, and reproducible—by spending compute only where the signal is. I bound peak scratch to ≈√N nodes, schedule high-value paths first, and cache the execution plan (not activations) for deterministic replay later.

What it buys me
	•	Bounded RAM by design. Peak scratch scales ≈ √N instead of N, so 8–16 GB laptops/phones can handle graphs that normally need workstations.
	•	Anytime results. I can stop early and still have a coherent answer; more time just refines "interesting" parts.
	•	Deterministic replay. Binary plans cache the execution recipe; I can reproduce the exact result later/on another box.
	•	Lower energy & cost. Recompute beats hoarding memory—great for edge, mobile, and cost-sensitive servers.

Where I use it (real-world)
	•	On-device AI / edge inference: retrieval, ranking, feature pipelines under hard memory ceilings.
	•	Search/RAG pipelines: pre-plan a query DAG; descend only into shards with high residual/novelty; cache the plan for popular queries.
	•	Code intelligence on huge repos: static analysis/refs with √N scratch; stream early results, get full fidelity if I let it run.
	•	Security scanning: CVE/secret scans with priority on recent/high-risk code; stay inside CI memory quotas.
	•	Data engineering on small boxes: transforms/joins over "too big" datasets via planning + spill + recompute.
	•	Scientific/geo: tiles/LiDAR/PDE-ish graphs—refine where error spikes, not the whole surface.
	•	Vision/video analytics: push depth into salient regions (motion/faces/text), keep backgrounds coarse—fits tight VRAM.
	•	Robotics & SLAM: bounded map updates on embedded hardware; refine high-uncertainty nodes only.
	•	Finance/backtesting: signals → features → strategies; drill into high-residual regimes; plans aid audit.
	•	Genomics/bio: large variant/annotation DAGs under strict RAM; reuse plan recipes across cohorts.

Two quick scenarios
	1.	RAG on a 12 GB laptop. Baseline O(N) memory trips on large corpora. Fractal-Down sets a √N cache (e.g., 256 nodes), evaluates high-salience shards first, spills/recomputes the rest. I get usable answers immediately; full fidelity if I let it finish. Next identical query replays instantly from the cached plan.
	2.	CI security scan with a 4 GB cap. Parse → tokenize → rules → report. With √N scratch and priority on "recent/critical" code, the job stays within memory limits and finishes predictably instead of failing or thrashing. Plans make recurring scans faster.

Who benefits

Data/ML engineers, product teams, SRE/platform, researchers, and robotics/embedded—anyone who needs strict memory envelopes without giving up correctness.

Bottom line: I turn memory into a safe constant—even on small devices—while steering compute where it matters most, and I make those choices portable and repeatable via cached plan recipes.

⸻

Related Work
	•	Square-root–space simulation (complexity theory). Williams shows any time-t multitape TM can be simulated in O(\sqrt{t\log t}) space, implying bounded-fan-in circuits of size s can be evaluated in \tilde{O}(\sqrt{s}) space—the theoretical backbone for √-space runtimes.
Link: https://arxiv.org/abs/2502.17779 (paper) and https://people.csail.mit.edu/rrw/time-vs-space.pdf (PDF).  ￼ ￼
	•	Gradient checkpointing (sublinear activation memory). Classic result trading recomputation for memory during backprop, achieving O(\sqrt{n}) activation memory.
Link: https://arxiv.org/abs/1604.06174 (paper).  ￼
	•	Revolve (optimal offline checkpoint schedules). Standard algorithm for adjoint/Reverse-AD checkpointing with principled time↔memory trade-offs.
Link: https://dl.acm.org/doi/10.1145/347837.347846 (TOMS) — PDF: https://dl.acm.org/doi/pdf/10.1145/347837.347846.  ￼
	•	Dynamic Tensor Rematerialization (online checkpointing). Greedy runtime policy that evicts/recomputes tensors; proves \Omega(\sqrt{N})-memory training for simple models; works with dynamic graphs.
Link: https://arxiv.org/abs/2006.09616 (paper) — PDF: https://ztatlock.net/pubs/2021-iclr-dtr/2021-iclr-dtr.pdf — OpenReview: https://openreview.net/forum?id=Vfs_2RnOD0H.  ￼ ￼ ￼
	•	Compiler memory planning (XLA). Compiler-level transformations that reshape compute to fit explicit memory limits ("memory-safe computations"), complementary to runtime policies.
Link: https://openreview.net/forum?id=2S_GtHBtTUP (paper) — overview: https://www.secondmind.ai/research/secondmind-papers/memory-safe-computations-with-xla-compiler.  ￼ ￼
	•	DAG engines with LRU/spilling. Dask's scheduler/worker implement cache-bounded execution and spill-to-disk thresholds—practical precedents for bounded-memory task graphs (not targeting √N or fractal priority).
Links: https://distributed.dask.org/en/stable/worker-memory.html and https://distributed.dask.org/en/latest/worker.html; GPU spilling: https://docs.rapids.ai/api/dask-cuda/stable/spilling/.  ￼ ￼
	•	Pebble games (I/O & memory lower bounds on DAGs). The red-blue pebble game formalizes cache size vs. recomputation (I/O complexity), framing limits of memory-constrained evaluations.
Links: https://www.eecs.harvard.edu/~htk/publication/1981-stoc-hong-kung.pdf (PDF) and https://dl.acm.org/doi/10.1145/800076.802486.  ￼ ￼
	•	Adaptive Computation Time (allocate compute where it matters). ACT learns to spend more steps on harder inputs—an architectural analogue of salience-gated descent.
Links: https://arxiv.org/abs/1603.08983 (paper) — PDF: https://openreview.net/pdf?id=r1W1OxAF.  ￼ ￼
	•	Adaptive Mesh Refinement & wavelets (refine "interesting" regions). AMR and wavelets concentrate resolution where local error is high—classical inspiration for fractal-down gating.
Links: Berger & Colella 1989 JCP: https://www.sciencedirect.com/science/article/pii/0021999189900351 (overview) — PDF mirror: https://crd.lbl.gov/assets/pubs_presos/AMCS/ANAG/A113.pdf; Mallat 1989 PAMI: https://www.di.ens.fr/~mallat/papiers/MallatTheory89.pdf.  ￼ ￼ ￼
	•	Tree Evaluation in near-log space (enabler for Williams). Cook & Mertz give a space-efficient algorithm for Tree Evaluation used inside the √-space time simulation.
Links: https://dl.acm.org/doi/10.1145/3618260.3649664 (STOC '24) — PDF: https://iuuk.mff.cuni.cz/~iwmertz/papers/cm24.tree_evaluation_is_in_space_lognloglogn.pdf.  ￼ ￼