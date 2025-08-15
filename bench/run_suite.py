"""
Main benchmark suite runner.

Executes benchmark scenarios, collects metrics, saves artifacts, and generates charts.
"""

import argparse
import sys
import math
from collections import OrderedDict
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

# Core fractal-down imports
from fractal_down.dag import DAG
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams
from fractal_down.cache import get_or_build_plan

# Bench imports
from bench.scenarios import scenario_tiny, scenario_synthetic, scenario_memory_stress, Job
from bench.metrics import track_peak_rss, measure_vram_peak, Timer, measure_energy, check_correctness
from bench.persist import new_run_dir, write_json, write_csv
from bench.graphs import generate_all_charts
from bench.system_info import collect_system_info


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for benchmark suite.
    
    Args:
        args: Optional command line arguments (for testing)
        
    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description='Fractal-Down benchmark and verification suite'
    )
    
    parser.add_argument('--scenarios', nargs='+', 
                       choices=['tiny', 'synthetic', 'memory-stress'],
                       default=['tiny', 'synthetic'],
                       help='Scenarios to run')
    
    parser.add_argument('--synthetic-n', type=int, default=200,
                       help='Number of nodes for synthetic scenario')
    
    parser.add_argument('--budgets', type=str,
                       help='Comma-separated budgets to override scenario defaults')
    
    parser.add_argument('--repeats', type=int, default=10,
                       help='Number of repeats per job')
    
    parser.add_argument('--outdir', type=str,
                       help='Output directory (default: artifacts/<timestamp>/)')
    
    parser.add_argument('--verify', action='store_true',
                       help='Enable evaluator verification')
    
    parser.add_argument('--payload-bytes', type=int, default=0,
                       help='Size of payload per node in bytes (default: 0, creates large intermediates for memory pressure)')
    
    parser.add_argument('--budget-sweep', action='store_true',
                       help='Auto-generate budgets around √N for scenario (overrides --budgets)')
    
    parser.add_argument('--clear-plan-cache', action='store_true',
                       help='Clear plan cache before running to measure cold performance')
    
    parser.add_argument('--memory-stress-mb', type=int, default=32,
                       help='Memory payload size in MB for memory-stress scenario (default: 32)')
    
    parser.add_argument('--dwell-ms', type=int, default=0,
                       help='Time in milliseconds to keep memory alive after computation (default: 0, helps capture peak RSS)')
    
    parser.add_argument('--rss-cap-mb', type=int, default=0,
                       help='RSS cap in MB for baseline-stress detection (default: 0=disabled, marks jobs that exceed this as CAP_EXCEEDED)')
    
    parsed_args = parser.parse_args(args)
    
    # Create run directory
    if parsed_args.outdir:
        run_dir = Path(parsed_args.outdir)
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir = new_run_dir()
    
    print(f"Benchmark run directory: {run_dir}")
    
    # Collect and save system info
    system_info = collect_system_info()
    write_json(system_info, run_dir / "system.json")
    print("System information saved")
    
    # Generate scenarios
    jobs = []
    
    if 'tiny' in parsed_args.scenarios:
        tiny_jobs = scenario_tiny(parsed_args.payload_bytes, parsed_args.dwell_ms)
        # Override repeats if specified
        if parsed_args.repeats != 5:  # 5 is default for tiny
            tiny_jobs = _override_repeats(tiny_jobs, parsed_args.repeats, 'tiny')
        jobs.extend(tiny_jobs)
        print(f"Generated {len(tiny_jobs)} tiny scenario jobs")
    
    if 'synthetic' in parsed_args.scenarios:
        synthetic_jobs = scenario_synthetic(parsed_args.synthetic_n, parsed_args.payload_bytes, parsed_args.dwell_ms)
        # Override repeats if specified
        if parsed_args.repeats != 10:  # 10 is default for synthetic
            synthetic_jobs = _override_repeats(synthetic_jobs, parsed_args.repeats, 'synthetic')
        jobs.extend(synthetic_jobs)
        print(f"Generated {len(synthetic_jobs)} synthetic scenario jobs")
    
    if 'memory-stress' in parsed_args.scenarios:
        memory_jobs = scenario_memory_stress(parsed_args.memory_stress_mb, parsed_args.dwell_ms)
        # Override repeats if specified
        if parsed_args.repeats != 10:  # 10 is default for memory-stress
            memory_jobs = _override_repeats(memory_jobs, parsed_args.repeats, 'memory-stress')
        jobs.extend(memory_jobs)
        print(f"Generated {len(memory_jobs)} memory-stress scenario jobs")
    
    # Override budgets if specified
    if parsed_args.budget_sweep:
        # Auto-generate budgets around √N for each scenario
        jobs = _apply_budget_sweep(jobs)
        print("Applied budget sweep (auto-generated budgets around √N)")
    elif parsed_args.budgets:
        try:
            custom_budgets = [int(b.strip()) for b in parsed_args.budgets.split(',')]
            jobs = _override_budgets(jobs, custom_budgets)
            print(f"Overrode budgets to: {custom_budgets}")
        except ValueError:
            print(f"Error: Invalid budget specification: {parsed_args.budgets}")
            return 1
    
    if not jobs:
        print("No jobs to run")
        return 1
    
    print(f"Running {len(jobs)} total jobs...")
    
    # Clear plan cache if requested (for cold performance testing)
    if parsed_args.clear_plan_cache:
        from fractal_down.cache import clear_cache
        clear_cache()
        print("Cleared plan cache for cold performance testing")
    
    # Run benchmark jobs
    results = []
    
    for i, job in enumerate(jobs):
        print(f"Running job {i+1}/{len(jobs)}: {job.name}")
        
        try:
            result = _run_single_job(job, parsed_args.verify, parsed_args.rss_cap_mb)
            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")
            # Record error result
            error_result = {
                'scenario': job.name.split('/')[0],
                'job': job.name,
                'mode': job.mode,
                'budget_nodes': job.budget_nodes,
                'repeat': _extract_repeat_number(job.name),
                'wall_s': 0.0,
                'cpu_s': 0.0,
                'peak_rss_bytes': 0,
                'peak_vram_bytes': 0,
                'energy_uj': "NA",
                'correct': False,
                'from_cache': False,
                'notes': str(e)[:200]  # Truncate long error messages
            }
            results.append(error_result)
    
    # Save results
    write_csv(results, run_dir / "results.csv")
    print(f"Results saved to {run_dir / 'results.csv'}")
    
    # Generate summary
    summary = _generate_summary(results)
    write_json(summary, run_dir / "summary.json")
    print(f"Summary saved to {run_dir / 'summary.json'}")
    
    # Generate charts
    try:
        generate_all_charts(results, run_dir)
    except Exception as e:
        print(f"Chart generation failed: {e}")
    
    # Print console summary
    _print_console_summary(results)
    
    print(f"\nBenchmark complete. Results in: {run_dir}")
    return 0


def _run_single_job(job: Job, verify: bool = False, rss_cap_mb: int = 0) -> Dict[str, Any]:
    """
    Run a single benchmark job and collect all metrics.
    
    Args:
        job: Job specification
        verify: Whether to enable verification
        rss_cap_mb: RSS cap in MB for baseline-stress detection (0=disabled)
        
    Returns:
        Dictionary with all collected metrics
    """
    result = {
        'scenario': job.name.split('/')[0],
        'job': job.name, 
        'mode': job.mode,
        'budget_nodes': job.budget_nodes,
        'repeat': _extract_repeat_number(job.name),
        'wall_s': 0.0,
        'cpu_s': 0.0,
        'peak_rss_bytes': 0,
        'peak_vram_bytes': 0,
        'energy_uj': "NA",
        'correct': False,
        'from_cache': False,
        'notes': "",
        # Plan characteristics (for sqrt mode)
        'unique_nodes': None,
        'order_len': None, 
        'recompute_factor': None
    }
    
    # Run with nested context managers for metrics collection
    with measure_energy() as energy_ctx:
        with measure_vram_peak() as vram_ctx:
            with track_peak_rss() as rss_ctx:
                with Timer() as timer_ctx:
                    
                    if job.mode == "baseline":
                        # Baseline: topological evaluation without caching/plans
                        baseline_result = _run_baseline(job.dag, job.root, job.inputs)
                        result['correct'] = True  # Baseline is always "correct"
                        result['from_cache'] = False
                        
                        # Force garbage collection and brief pause to ensure RSS measurement
                        import gc, time
                        gc.collect()
                        time.sleep(0.01)
                        
                        # Add dwell time if specified to keep memory alive for measurement
                        if job.dwell_ms > 0:
                            time.sleep(job.dwell_ms / 1000.0)
                        
                    elif job.mode == "sqrt":
                        # √N+fractal: build plan and use evaluator
                        sqrt_result, was_cached, plan = _run_sqrt(job.dag, job.root, job.inputs, 
                                                           job.budget_nodes, verify)
                        
                        # Force garbage collection and brief pause to ensure RSS measurement
                        import gc, time
                        gc.collect()
                        time.sleep(0.01)
                        
                        # Add dwell time if specified to keep memory alive for measurement
                        if job.dwell_ms > 0:
                            time.sleep(job.dwell_ms / 1000.0)
                        
                        # Extract plan characteristics
                        unique_nodes = len(set(plan.order))
                        order_len = len(plan.order)
                        recompute_factor = order_len / unique_nodes if unique_nodes > 0 else 1.0
                        
                        result['unique_nodes'] = unique_nodes
                        result['order_len'] = order_len
                        result['recompute_factor'] = recompute_factor
                        
                        # Check correctness against baseline if possible
                        baseline_result = _run_baseline(job.dag, job.root, job.inputs)
                        result['correct'] = check_correctness(baseline_result.digest, sqrt_result.digest)
                        result['from_cache'] = was_cached
                    
                    else:
                        raise ValueError(f"Unknown mode: {job.mode}")
    
    # Extract metrics from context managers
    result.update(timer_ctx)
    result.update(rss_ctx)
    result.update(vram_ctx) 
    result.update(energy_ctx)
    
    # Add RSS cap information to results
    result['rss_cap_mb'] = rss_cap_mb
    
    # Check RSS cap if specified
    if rss_cap_mb > 0:
        rss_cap_bytes = rss_cap_mb * 1024 * 1024
        rss_cap_exceeded = result.get('peak_rss_bytes', 0) > rss_cap_bytes
        result['rss_cap_exceeded'] = rss_cap_exceeded
        if rss_cap_exceeded:
            result['notes'] = f"CAP_EXCEEDED (peak_rss={result.get('peak_rss_bytes', 0)/1024/1024:.1f}MB > cap={rss_cap_mb}MB)"
    else:
        result['rss_cap_exceeded'] = False
    
    # Add cache state for cold vs warm labeling
    if job.mode == "sqrt":
        result['cache_state'] = 'warm' if result.get('from_cache', False) else 'cold'
    else:
        result['cache_state'] = 'baseline'
    
    return result


def _run_baseline(dag: DAG, root: int, inputs: Dict[int, Any]):
    """
    Run baseline topological evaluation without caching or plans.
    
    This is the reference implementation that computes each node exactly once
    in topological order without any memory constraints.
    """
    # Simple topological evaluation
    computed = {}
    
    def compute_node(node_id: int):
        if node_id in computed:
            return computed[node_id]
            
        node = dag.node(node_id)
        
        if node.op is None:
            # Leaf node - get from inputs
            if node_id not in inputs:
                raise ValueError(f"Missing input for leaf node {node_id}")
            value = inputs[node_id]
        else:
            # Operation node - compute dependencies first
            dep_values = []
            for dep_id in node.inputs:
                dep_values.append(compute_node(dep_id))
            
            # Apply operation
            if len(dep_values) == 1:
                value = node.op(dep_values[0])
            elif len(dep_values) == 2:
                value = node.op(dep_values[0], dep_values[1])
            else:
                # Variable arity - use functools.reduce for associative ops
                import functools
                if hasattr(node.op, '__name__') and node.op.__name__ in ['add', 'mul']:
                    value = functools.reduce(node.op, dep_values)
                else:
                    # For other ops, apply pairwise
                    value = dep_values[0]
                    for dep_val in dep_values[1:]:
                        value = node.op(value, dep_val)
        
        computed[node_id] = value
        return value
    
    # Compute root
    final_value = compute_node(root)
    
    # Create a result similar to EvalResult
    from fractal_down.hashing import get_default_provider
    hash_provider = get_default_provider()
    
    # Serialize value for digest
    import json
    try:
        value_bytes = json.dumps(final_value, sort_keys=True).encode('utf-8')
    except (TypeError, ValueError):
        value_bytes = str(final_value).encode('utf-8')
    
    digest = hash_provider.digest(value_bytes)
    
    class BaselineResult:
        def __init__(self, value, digest):
            self.value = value
            self.digest = digest
    
    return BaselineResult(final_value, digest)


def _run_sqrt(dag: DAG, root: int, inputs: Dict[int, Any], 
              budget_nodes: int, verify: bool = False):
    """
    Run √N+fractal evaluation with plan building and caching.
    
    Returns:
        Tuple of (EvalResult, was_cached, Plan)
    """
    # Compute priorities
    params = FractalParams()
    priorities = compute_node_priority(dag, root, params)
    
    # Build plan function
    def build_fn():
        return build_plan(dag, root, budget_nodes=budget_nodes, node_priority=priorities)
    
    # Get or build cached plan
    plan, cache_path, was_cached = get_or_build_plan(dag, root, budget_nodes, build_fn, params)
    
    # Evaluate with the plan
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=verify)
    
    return result, was_cached, plan


def _extract_repeat_number(job_name: str) -> int:
    """Extract repeat number from job name."""
    parts = job_name.split('/')
    for part in parts:
        if part.startswith('repeat_'):
            try:
                return int(part.split('_')[1])
            except (IndexError, ValueError):
                pass
    return 0


def _override_repeats(jobs: List[Job], new_repeats: int, scenario_prefix: str) -> List[Job]:
    """Override the number of repeats for jobs."""
    # Group jobs by (mode, budget)
    job_groups = {}
    for job in jobs:
        if not job.name.startswith(scenario_prefix):
            continue
        
        key = (job.mode, job.budget_nodes)
        if key not in job_groups:
            job_groups[key] = []
        job_groups[key].append(job)
    
    # Create new jobs with desired number of repeats
    new_jobs = []
    for job in jobs:
        if not job.name.startswith(scenario_prefix):
            new_jobs.append(job)
            continue
            
        # Only keep first job from each group and replicate
        key = (job.mode, job.budget_nodes)
        group_jobs = job_groups.get(key, [])
        
        if group_jobs and job == group_jobs[0]:
            # This is the first job in the group - replicate it
            for repeat in range(new_repeats):
                new_job = Job(
                    name=f"{scenario_prefix}/{job.mode}/repeat_{repeat}".replace("baseline/", "baseline/").replace("sqrt-", "sqrt-"),
                    mode=job.mode,
                    budget_nodes=job.budget_nodes,
                    dag=job.dag,
                    root=job.root,
                    inputs=job.inputs,
                    dwell_ms=job.dwell_ms
                )
                # Fix name formatting
                if job.mode == "sqrt" and job.budget_nodes is not None:
                    new_job.name = f"{scenario_prefix}/sqrt-{job.budget_nodes}/repeat_{repeat}"
                elif job.mode == "baseline":
                    new_job.name = f"{scenario_prefix}/baseline/repeat_{repeat}"
                
                new_jobs.append(new_job)
    
    return new_jobs


def _override_budgets(jobs: List[Job], budgets: List[int]) -> List[Job]:
    """Override budgets for sqrt mode jobs."""
    new_jobs = []
    
    # Keep all baseline jobs
    baseline_jobs = [job for job in jobs if job.mode == "baseline"]
    new_jobs.extend(baseline_jobs)
    
    # Group sqrt jobs by scenario
    sqrt_job_templates = {}
    for job in jobs:
        if job.mode == "sqrt":
            scenario = job.name.split('/')[0]
            if scenario not in sqrt_job_templates:
                sqrt_job_templates[scenario] = job
    
    # Create new sqrt jobs with custom budgets
    for scenario, template in sqrt_job_templates.items():
        for budget in budgets:
            # Count number of baseline repeats for this scenario
            baseline_count = len([j for j in baseline_jobs if j.name.startswith(scenario + "/")])
            
            for repeat in range(baseline_count):
                new_job = Job(
                    name=f"{scenario}/sqrt-{budget}/repeat_{repeat}",
                    mode="sqrt",
                    budget_nodes=budget,
                    dag=template.dag,
                    root=template.root,
                    inputs=template.inputs,
                    dwell_ms=template.dwell_ms
                )
                new_jobs.append(new_job)
    
    return new_jobs


def _apply_budget_sweep(jobs: List[Job]) -> List[Job]:
    """Apply budget sweep - auto-generate budgets around √N for each scenario."""
    import math
    
    new_jobs = []
    
    # Keep all baseline jobs
    baseline_jobs = [job for job in jobs if job.mode == "baseline"]
    new_jobs.extend(baseline_jobs)
    
    # Group sqrt jobs by scenario and determine optimal budgets
    sqrt_job_templates = {}
    for job in jobs:
        if job.mode == "sqrt":
            scenario = job.name.split('/')[0]
            if scenario not in sqrt_job_templates:
                sqrt_job_templates[scenario] = job
    
    # For each scenario, compute √N and create budget sweep
    for scenario, template in sqrt_job_templates.items():
        # Get number of nodes in DAG
        n_nodes = len(template.dag.postorder(template.root))
        sqrt_n = math.ceil(math.sqrt(n_nodes))
        
        # Generate budgets: [√N/2, √N, 2√N]  
        budgets = [
            max(1, sqrt_n // 2),
            sqrt_n,
            2 * sqrt_n
        ]
        
        # Count baseline repeats for this scenario  
        baseline_count = len([j for j in baseline_jobs if j.name.startswith(scenario + "/")])
        
        for budget in budgets:
            for repeat in range(baseline_count):
                new_job = Job(
                    name=f"{scenario}/sqrt-{budget}/repeat_{repeat}",
                    mode="sqrt",
                    budget_nodes=budget,
                    dag=template.dag,
                    root=template.root,
                    inputs=template.inputs,
                    dwell_ms=template.dwell_ms
                )
                new_jobs.append(new_job)
    
    return new_jobs


def _generate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics from results."""
    summary = {
        "total_jobs": len(results),
        "scenarios": {},
        "non_goals_note": "Not a distributed scheduler - single process only. Slowdown is expected but should be predictable. Tune FractalParams per domain for best results."
    }
    
    # Group by scenario, mode, budget
    groups = {}
    for result in results:
        scenario = result.get('scenario', 'unknown')
        mode = result.get('mode', 'unknown')
        budget = result.get('budget_nodes', 'baseline')
        
        key = (scenario, mode, budget)
        if key not in groups:
            groups[key] = []
        groups[key].append(result)
    
    # Calculate aggregates
    for (scenario, mode, budget), group_results in groups.items():
        if scenario not in summary["scenarios"]:
            summary["scenarios"][scenario] = {}
        
        mode_budget_key = f"{mode}" + (f"-{budget}" if budget != "baseline" and budget is not None else "")
        
        # Calculate min/mean/max/median/std for numeric fields
        numeric_fields = ['peak_rss_bytes', 'peak_vram_bytes', 'wall_s', 'cpu_s']
        aggregates = {}
        
        for field in numeric_fields:
            values = [r.get(field, 0) for r in group_results if isinstance(r.get(field), (int, float)) and r.get(field, 0) > 0]
            if values:
                import statistics
                aggregates[field] = {
                    'min': min(values),
                    'mean': sum(values) / len(values),
                    'max': max(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'count': len(values)
                }
            else:
                aggregates[field] = {'min': 0, 'mean': 0, 'max': 0, 'median': 0, 'std': 0, 'count': 0}
        
        # Handle energy separately (can be "NA")
        energy_values = []
        for r in group_results:
            energy = r.get('energy_uj')
            if energy != "NA" and isinstance(energy, (int, float)):
                energy_values.append(energy)
        
        if energy_values:
            import statistics
            aggregates['energy_uj'] = {
                'min': min(energy_values),
                'mean': sum(energy_values) / len(energy_values),
                'max': max(energy_values),
                'median': statistics.median(energy_values),
                'std': statistics.stdev(energy_values) if len(energy_values) > 1 else 0,
                'count': len(energy_values)
            }
        else:
            aggregates['energy_uj'] = "NA"
        
        # Calculate rates
        total_jobs = len(group_results)
        correct_jobs = sum(1 for r in group_results if r.get('correct', False))
        cached_jobs = sum(1 for r in group_results if r.get('from_cache', False))
        
        aggregates['parity_percent'] = (correct_jobs / total_jobs * 100) if total_jobs > 0 else 0
        aggregates['cache_hit_rate_percent'] = (cached_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        summary["scenarios"][scenario][mode_budget_key] = aggregates
    
    return summary


def _print_console_summary(results: List[Dict[str, Any]]) -> None:
    """Print a brief console summary of key results."""
    print("\n=== BENCHMARK SUMMARY ===")
    
    # Group results
    baseline_times = {}
    sqrt_times = {}
    
    for result in results:
        scenario = result.get('scenario', 'unknown')
        mode = result.get('mode', 'unknown')
        wall_s = result.get('wall_s', 0)
        
        if wall_s <= 0:
            continue
            
        if mode == 'baseline':
            if scenario not in baseline_times:
                baseline_times[scenario] = []
            baseline_times[scenario].append(wall_s)
        elif mode == 'sqrt':
            budget = result.get('budget_nodes', 'unknown')
            key = (scenario, budget)
            if key not in sqrt_times:
                sqrt_times[key] = []
            sqrt_times[key].append(wall_s)
    
    # Calculate and print slowdown factors with variance
    print("\nSlowdown factors (sqrt/baseline):")
    for (scenario, budget), sqrt_time_list in sqrt_times.items():
        if scenario in baseline_times and sqrt_time_list:
            import statistics
            sqrt_median = statistics.median(sqrt_time_list)
            baseline_median = statistics.median(baseline_times[scenario]) if baseline_times[scenario] else 1
            
            if baseline_median > 0:
                slowdown = sqrt_median / baseline_median
                sqrt_std = statistics.stdev(sqrt_time_list) if len(sqrt_time_list) > 1 else 0
                baseline_std = statistics.stdev(baseline_times[scenario]) if len(baseline_times[scenario]) > 1 else 0
                
                # Show variance info if we have enough samples
                if len(sqrt_time_list) > 2 and sqrt_std > 0:
                    cv = sqrt_std / sqrt_median * 100  # coefficient of variation
                    print(f"  {scenario} budget={budget}: {slowdown:.2f}x (std={sqrt_std*1000:.1f}ms, CV={cv:.1f}%)")
                else:
                    print(f"  {scenario} budget={budget}: {slowdown:.2f}x")
    
    # Memory usage by mode
    rss_values = [r.get('peak_rss_bytes', 0) for r in results if r.get('peak_rss_bytes', 0) > 0]
    delta_rss_values = [r.get('delta_rss_bytes', 0) for r in results if r.get('delta_rss_bytes', 0) > 0]
    baseline_delta_rss = [r.get('delta_rss_bytes', 0) for r in results if r.get('mode') == 'baseline' and r.get('delta_rss_bytes', 0) > 0]
    sqrt_delta_rss = [r.get('delta_rss_bytes', 0) for r in results if r.get('mode') == 'sqrt' and r.get('delta_rss_bytes', 0) > 0]
    
    if rss_values:
        avg_rss_mb = sum(rss_values) / len(rss_values) / (1024*1024)
        print(f"\nAverage peak RSS: {avg_rss_mb:.1f} MB")
    
    if delta_rss_values:
        avg_delta_rss_mb = sum(delta_rss_values) / len(delta_rss_values) / (1024*1024)
        print(f"Average delta RSS: {avg_delta_rss_mb:.1f} MB")
        
        if baseline_delta_rss and sqrt_delta_rss:
            baseline_avg = sum(baseline_delta_rss) / len(baseline_delta_rss) / (1024*1024)
            sqrt_avg = sum(sqrt_delta_rss) / len(sqrt_delta_rss) / (1024*1024)
            savings = ((baseline_avg - sqrt_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
            print(f"  Baseline delta RSS: {baseline_avg:.1f} MB")
            print(f"  √N delta RSS: {sqrt_avg:.1f} MB ({savings:+.1f}% vs baseline)")
    
    # RSS cap violations (make them highly visible)
    cap_exceeded_jobs = [r for r in results if 'CAP_EXCEEDED' in r.get('notes', '')]
    if cap_exceeded_jobs:
        print(f"\n⚠️  RSS CAP VIOLATIONS:")
        for job in cap_exceeded_jobs:
            print(f"    {job.get('job', 'unknown')}: {job.get('notes', '')}")
    
    # Correctness
    total_correctness_jobs = sum(1 for r in results if 'correct' in r)
    correct_jobs = sum(1 for r in results if r.get('correct', False))
    if total_correctness_jobs > 0:
        parity_pct = correct_jobs / total_correctness_jobs * 100
        print(f"Correctness: {correct_jobs}/{total_correctness_jobs} ({parity_pct:.1f}%)")
    
    # Cache hits with warm/cold breakdown
    sqrt_jobs = [r for r in results if r.get('mode') == 'sqrt']
    if sqrt_jobs:
        cache_hits = sum(1 for r in sqrt_jobs if r.get('from_cache', False))
        cache_misses = len(sqrt_jobs) - cache_hits
        cache_rate = cache_hits / len(sqrt_jobs) * 100
        print(f"Cache performance: {cache_hits} hits, {cache_misses} misses ({cache_rate:.1f}% hit rate)")
        
        # Show timing difference between cold and warm
        cold_times = [r.get('wall_s', 0) for r in sqrt_jobs if not r.get('from_cache', False) and r.get('wall_s', 0) > 0]
        warm_times = [r.get('wall_s', 0) for r in sqrt_jobs if r.get('from_cache', False) and r.get('wall_s', 0) > 0]
        
        if cold_times and warm_times:
            import statistics
            cold_median = statistics.median(cold_times)
            warm_median = statistics.median(warm_times)
            speedup = cold_median / warm_median if warm_median > 0 else 1
            
            # Show detailed stats if we have enough data
            if len(cold_times) > 1 and len(warm_times) > 1:
                cold_std = statistics.stdev(cold_times)
                warm_std = statistics.stdev(warm_times)
                print(f"  Cold (plan build): {cold_median*1000:.1f}ms median (±{cold_std*1000:.1f}ms), Warm (cached): {warm_median*1000:.1f}ms median (±{warm_std*1000:.1f}ms) → {speedup:.1f}x speedup")
            else:
                print(f"  Cold (plan build): {cold_median*1000:.1f}ms median, Warm (cached): {warm_median*1000:.1f}ms median → {speedup:.1f}x speedup")

    # Plan Statistics (recompute factors) 
    print("\nPlan Statistics (recompute factors):")
    scenario_plan_stats = {}
    for r in results:
        if r.get('mode') == 'sqrt' and r.get('recompute_factor') is not None:
            scenario = r.get('scenario', 'unknown')
            budget = r.get('budget_nodes', 'unknown')
            key = f"{scenario} budget={budget}"
            
            if key not in scenario_plan_stats:
                scenario_plan_stats[key] = []
            scenario_plan_stats[key].append(r.get('recompute_factor', 1.0))
    
    for key, factors in scenario_plan_stats.items():
        if factors:
            avg_factor = sum(factors) / len(factors)
            print(f"  {key}: {avg_factor:.2f}x recompute (higher = more recomputation)")

    # Add non-goals note
    print(f"\nNote: Slowdown is expected but bounded. √N+fractal trades speed for memory.")
    print(f"Not a distributed scheduler - single process only. Tune FractalParams per domain.")


if __name__ == "__main__":
    sys.exit(main())