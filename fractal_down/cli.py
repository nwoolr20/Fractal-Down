# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Command-line interface for fractal-down.

Provides commands for building plans, evaluating DAGs, and managing the cache.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from fractal_down.dag import DAG
from fractal_down.treelift import build_plan, Plan
from fractal_down.evaluator import Evaluator, EvalResult
from fractal_down.fractal import compute_node_priority, FractalParams
from fractal_down.binary_plan import save_plan, load_plan
from fractal_down.cache import get_cache_dir, get_or_build_plan
from fractal_down.examples import make_tiny_dag, demo_run
from fractal_down.license_key import generate_license, verify_license


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="fd",
        description="Fractal-Down: DAG evaluation with √N memory and fractal priority",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init-sample command
    init_parser = subparsers.add_parser(
        "init-sample", help="Initialize sample DAG and print details"
    )

    # build-plan command
    build_parser = subparsers.add_parser(
        "build-plan", help="Build and save execution plan"
    )
    build_parser.add_argument(
        "--budget", type=int, required=True, help="Memory budget (number of nodes)"
    )
    build_parser.add_argument(
        "--save", type=str, required=True, help="Path to save plan file"
    )
    build_parser.add_argument(
        "--root", type=int, required=True, help="Root node ID to evaluate"
    )

    # eval command
    eval_parser = subparsers.add_parser("eval", help="Evaluate DAG with given budget")
    eval_parser.add_argument(
        "--budget", type=int, required=True, help="Memory budget (number of nodes)"
    )
    eval_parser.add_argument(
        "--verify", action="store_true", help="Enable verification mode"
    )

    # inspect-plan command
    inspect_parser = subparsers.add_parser(
        "inspect-plan", help="Inspect saved plan file"
    )
    inspect_parser.add_argument("path", help="Path to plan file")

    # clear-cache command
    clear_parser = subparsers.add_parser("clear-cache", help="Clear cached plans")
    clear_parser.add_argument("--days", type=int, help="Remove plans older than N days")
    clear_parser.add_argument("--count", type=int, help="Keep only N newest plans")

    # license command
    lic_parser = subparsers.add_parser("license", help="Manage license keys")
    lic_sub = lic_parser.add_subparsers(dest="license_cmd")

    lic_issue = lic_sub.add_parser("issue", help="Generate a license key")
    lic_issue.add_argument("--contract", required=True, help="Contract identifier")

    lic_check = lic_sub.add_parser("check", help="Verify a license key")
    lic_check.add_argument("key", help="License key to check")

    # bench command
    bench_parser = subparsers.add_parser(
        "bench", help="Run benchmark and verification suite"
    )
    bench_parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=["tiny", "synthetic", "memory-stress"],
        default=["tiny", "synthetic"],
        help="Scenarios to run",
    )
    bench_parser.add_argument(
        "--synthetic-n",
        type=int,
        default=200,
        help="Number of nodes for synthetic scenario",
    )
    bench_parser.add_argument(
        "--budgets",
        type=str,
        help="Comma-separated budgets to override scenario defaults",
    )
    bench_parser.add_argument(
        "--repeats", type=int, default=10, help="Number of repeats per job"
    )
    bench_parser.add_argument(
        "--verify", action="store_true", help="Enable evaluator verification"
    )
    bench_parser.add_argument(
        "--outdir", type=str, help="Output directory (default: artifacts/<timestamp>/)"
    )
    bench_parser.add_argument(
        "--payload-bytes",
        type=int,
        default=0,
        help="Size of payload per node in bytes (default: 0)",
    )
    bench_parser.add_argument(
        "--dwell-ms",
        type=int,
        default=0,
        help="Time in milliseconds to keep memory alive after computation (default: 0)",
    )
    bench_parser.add_argument(
        "--rss-cap-mb",
        type=int,
        default=0,
        help="RSS cap in MB for baseline-stress detection (default: 0=disabled)",
    )
    bench_parser.add_argument(
        "--memory-stress-mb",
        type=int,
        default=32,
        help="Memory payload size in MB for memory-stress scenario (default: 32)",
    )
    bench_parser.add_argument(
        "--budget-sweep",
        action="store_true",
        help="Auto-generate budgets around √N for scenario",
    )
    bench_parser.add_argument(
        "--clear-plan-cache",
        action="store_true",
        help="Clear plan cache before running",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    try:
        if args.command == "init-sample":
            return cmd_init_sample()
        elif args.command == "build-plan":
            return cmd_build_plan(args.budget, args.save, args.root)
        elif args.command == "eval":
            return cmd_eval(args.budget, args.verify)
        elif args.command == "inspect-plan":
            return cmd_inspect_plan(args.path)
        elif args.command == "clear-cache":
            return cmd_clear_cache(args.days, args.count)
        elif args.command == "license":
            return cmd_license(args)
        elif args.command == "bench":
            return cmd_bench(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_init_sample() -> int:
    """Initialize sample DAG and print details."""
    print("Creating sample DAG...")
    dag, root, inputs = make_tiny_dag()

    print(f"Sample DAG created with {dag.size()} nodes")
    print(f"Root node ID: {root}")
    print("\nNode details:")

    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        if node.op is None:
            value = inputs.get(node_id, "N/A")
            print(f"  {node_id}: {node.name} (leaf, value={value})")
        else:
            op_name = getattr(node.op, "__name__", str(node.op))
            print(f"  {node_id}: {node.name} = {op_name}({list(node.inputs)})")

    print(f"\nExpected result: {(inputs[0] + inputs[1]) * (inputs[2] + inputs[3])}")
    print(f"Use 'fd eval --budget 2 --verify' to evaluate this DAG")

    return 0


def cmd_build_plan(budget: int, save_path: str, root_id: int) -> int:
    """Build and save execution plan."""
    print("Creating sample DAG...")
    dag, actual_root, inputs = make_tiny_dag()

    # Validate root ID
    if root_id not in dag._nodes:
        print(f"Error: Root node {root_id} does not exist in DAG", file=sys.stderr)
        print(f"Available nodes: {sorted(dag._nodes.keys())}")
        return 1

    # Use provided root instead of default
    root = root_id

    print(f"Building plan for root {root} with budget {budget}...")

    # Compute priorities
    params = FractalParams()
    priorities = compute_node_priority(dag, root, params)

    # Build plan
    plan = build_plan(dag, root, budget_nodes=budget, node_priority=priorities)

    print(f"Plan built:")
    print(f"  Root: {plan.root}")
    print(f"  Budget: {plan.budget_nodes}")
    print(f"  Order length: {len(plan.order)}")
    print(f"  Order: {plan.order}")

    # Save plan
    saved_path = save_plan(plan, save_path)
    print(f"Plan saved to: {saved_path}")

    return 0


def cmd_eval(budget: int, verify: bool) -> int:
    """Evaluate DAG with given budget."""
    print("Creating sample DAG...")
    dag, root, inputs = make_tiny_dag()

    print(f"Evaluating with budget {budget}, verify={verify}")

    # Compute priorities and build plan
    params = FractalParams()
    priorities = compute_node_priority(dag, root, params)

    def build_fn():
        return build_plan(dag, root, budget_nodes=budget, node_priority=priorities)

    # Get or build cached plan
    plan, cache_path, was_cached = get_or_build_plan(
        dag, root, budget, build_fn, params
    )

    print(
        f"Plan {'loaded from cache' if was_cached else 'built and cached'}: {cache_path}"
    )
    print(f"Plan order length: {len(plan.order)}")

    # Evaluate
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=verify)

    print(f"Result: {result.value}")
    print(f"Digest: {result.digest.hex()}")

    return 0


def cmd_inspect_plan(path: str) -> int:
    """Inspect saved plan file."""
    try:
        plan = load_plan(path)
        print(f"Plan file: {path}")
        print(f"Root: {plan.root}")
        print(f"Budget: {plan.budget_nodes}")
        print(f"Order length: {len(plan.order)}")
        print(f"Order: {plan.order}")
        return 0

    except (ValueError, IOError) as e:
        print(f"Error loading plan: {e}", file=sys.stderr)
        return 1


def cmd_clear_cache(days: Optional[int], count: Optional[int]) -> int:
    """Clear cached plans."""
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        print("No cache directory found")
        return 0

    # Get all plan files
    plan_files = list(cache_dir.glob("*.fplan"))

    if not plan_files:
        print("No cached plans found")
        return 0

    # Determine which files to remove
    files_to_remove = []

    if days is not None:
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        for plan_file in plan_files:
            try:
                if plan_file.stat().st_mtime < cutoff_time:
                    files_to_remove.append(plan_file)
            except OSError:
                continue

    elif count is not None:
        # Keep only N newest files
        plan_files_with_time = []
        for plan_file in plan_files:
            try:
                mtime = plan_file.stat().st_mtime
                plan_files_with_time.append((mtime, plan_file))
            except OSError:
                continue

        # Sort by modification time, newest first
        plan_files_with_time.sort(key=lambda x: x[0], reverse=True)

        # Remove files beyond the count
        files_to_remove = [f for _, f in plan_files_with_time[count:]]

    else:
        # Remove all files
        files_to_remove = plan_files

    # Remove the files
    removed_count = 0
    for plan_file in files_to_remove:
        try:
            plan_file.unlink()
            removed_count += 1
        except OSError:
            continue

    print(f"Removed {removed_count} cached plan files")
    remaining = len(plan_files) - removed_count
    print(f"{remaining} files remaining in cache")

    return 0


def cmd_license(args) -> int:
    """Issue or verify license keys."""
    if args.license_cmd == "issue":
        record = generate_license(args.contract)
        print(f"Issued license key: {record.key}")
        return 0
    elif args.license_cmd == "check":
        if verify_license(args.key):
            print("License key valid")
            return 0
        else:
            print("License key invalid")
            return 1
    else:
        print("No license action specified")
        return 1


def cmd_bench(args) -> int:
    """Run benchmark and verification suite."""
    try:
        import os

        # Add the parent directory to Python path to import bench
        repo_root = Path(__file__).parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        import bench.run_suite

        # Convert argparse Namespace to list of arguments for bench.run_suite.main()
        bench_args = []

        if args.scenarios != ["tiny", "synthetic"]:  # Non-default
            bench_args.extend(["--scenarios"] + args.scenarios)

        if args.synthetic_n != 200:  # Non-default
            bench_args.extend(["--synthetic-n", str(args.synthetic_n)])

        if args.budgets:
            bench_args.extend(["--budgets", args.budgets])

        if args.repeats != 10:  # Non-default
            bench_args.extend(["--repeats", str(args.repeats)])

        if args.verify:
            bench_args.append("--verify")

        if args.outdir:
            bench_args.extend(["--outdir", args.outdir])

        # Forward additional parameters
        if hasattr(args, "payload_bytes") and args.payload_bytes != 0:
            bench_args.extend(["--payload-bytes", str(args.payload_bytes)])

        if hasattr(args, "dwell_ms") and args.dwell_ms != 0:
            bench_args.extend(["--dwell-ms", str(args.dwell_ms)])

        if hasattr(args, "rss_cap_mb") and args.rss_cap_mb != 0:
            bench_args.extend(["--rss-cap-mb", str(args.rss_cap_mb)])

        if hasattr(args, "memory_stress_mb") and args.memory_stress_mb != 32:
            bench_args.extend(["--memory-stress-mb", str(args.memory_stress_mb)])

        if hasattr(args, "budget_sweep") and args.budget_sweep:
            bench_args.append("--budget-sweep")

        if hasattr(args, "clear_plan_cache") and args.clear_plan_cache:
            bench_args.append("--clear-plan-cache")

        return bench.run_suite.main(bench_args)

    except ImportError as e:
        print(f"Error: bench module not available: {e}", file=sys.stderr)
        print(
            "Try installing optional dependencies: pip install -e .[bench]",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
