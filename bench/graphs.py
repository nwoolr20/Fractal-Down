# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Chart generation for benchmark visualization.

Creates PNG charts showing memory usage, slowdown factors, correctness,
cache reuse, and energy consumption.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    np = None
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False


def generate_all_charts(data: Union[List[Dict[str, Any]], 'pd.DataFrame'], 
                       run_dir: Union[str, Path]) -> None:
    """
    Generate all benchmark charts and save to run directory.
    
    Args:
        data: Benchmark results data (list of dicts or DataFrame)
        run_dir: Directory to save charts
    """
    if not HAS_MATPLOTLIB:
        print("matplotlib not available - generating simple text/HTML charts instead")
        try:
            from bench.simple_charts import generate_simple_charts
            # Convert DataFrame to list of dicts if needed
            if HAS_PANDAS and hasattr(data, 'to_dict'):
                data_list = data.to_dict('records')
            else:
                data_list = data
            generate_simple_charts(data_list, run_dir)
            return
        except ImportError:
            print("Simple charts fallback not available - skipping chart generation")
            return
    
    run_dir = Path(run_dir)
    
    # Convert data to common format
    if HAS_PANDAS and hasattr(data, 'iterrows'):
        # It's a DataFrame
        df_data = data
    else:
        # It's a list of dicts, convert to simple processing format
        df_data = data
    
    try:
        generate_memory_peak_chart(df_data, run_dir / "memory_peak.png")
        generate_slowdown_chart(df_data, run_dir / "slowdown_vs_budget.png") 
        generate_correctness_chart(df_data, run_dir / "correctness.png")
        generate_cache_reuse_chart(df_data, run_dir / "cache_reuse.png")
        generate_energy_chart(df_data, run_dir / "energy_vs_mode.png")
        print(f"Charts saved to {run_dir}")
    except Exception as e:
        print(f"Error generating charts: {e}")


def generate_memory_peak_chart(data: Union[List[Dict], 'pd.DataFrame'], 
                              output_path: Union[str, Path]) -> None:
    """Generate peak RSS and VRAM vs (mode,budget) by scenario."""
    if not HAS_MATPLOTLIB:
        return
    
    # Parse data
    if HAS_PANDAS and hasattr(data, 'groupby'):
        df = data
    else:
        # Manual processing
        scenarios = set()
        modes = set()
        budgets = set()
        
        for row in data:
            scenarios.add(row.get('scenario', 'unknown'))
            modes.add(row.get('mode', 'unknown'))
            if row.get('budget_nodes') is not None:
                budgets.add(row.get('budget_nodes'))
        
        scenarios = sorted(scenarios)
        modes = sorted(modes)
        budgets = sorted(b for b in budgets if b is not None)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Peak RSS chart
    ax1 = axes[0]
    _plot_memory_by_scenario(data, 'peak_rss_bytes', ax1, "Peak RSS (MB)")
    
    # Peak VRAM chart  
    ax2 = axes[1]
    _plot_memory_by_scenario(data, 'peak_vram_bytes', ax2, "Peak VRAM (MB)")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()


def generate_slowdown_chart(data: Union[List[Dict], 'pd.DataFrame'],
                           output_path: Union[str, Path]) -> None:
    """Generate slowdown factor = time_sqrt / time_baseline vs budget by scenario."""
    if not HAS_MATPLOTLIB:
        return
    
    # Calculate slowdown factors
    slowdowns = _calculate_slowdowns(data)
    
    if not slowdowns:
        # Create empty chart with message
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No slowdown data available", 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title("Slowdown vs Budget")
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    scenarios = sorted(set(s['scenario'] for s in slowdowns))
    colors = plt.cm.Set1(np.linspace(0, 1, len(scenarios)))
    
    for i, scenario in enumerate(scenarios):
        scenario_data = [s for s in slowdowns if s['scenario'] == scenario]
        if scenario_data:
            budgets = [s['budget'] for s in scenario_data]
            factors = [s['slowdown_factor'] for s in scenario_data]
            ax.plot(budgets, factors, 'o-', label=scenario, color=colors[i])
    
    ax.set_xlabel("Budget (nodes)")
    ax.set_ylabel("Slowdown factor (sqrt/baseline)")
    ax.set_title("Slowdown vs Budget")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()


def generate_correctness_chart(data: Union[List[Dict], 'pd.DataFrame'],
                              output_path: Union[str, Path]) -> None:
    """Generate correctness pass/fail counts."""
    if not HAS_MATPLOTLIB:
        return
    
    # Count correctness by scenario and mode
    counts = {}
    
    if HAS_PANDAS and hasattr(data, 'groupby'):
        grouped = data.groupby(['scenario', 'mode'])['correct'].agg(['sum', 'count']).reset_index()
        for _, row in grouped.iterrows():
            key = (row['scenario'], row['mode'])
            counts[key] = {'correct': row['sum'], 'total': row['count']}
    else:
        for row in data:
            key = (row.get('scenario', 'unknown'), row.get('mode', 'unknown'))
            if key not in counts:
                counts[key] = {'correct': 0, 'total': 0}
            counts[key]['total'] += 1
            if row.get('correct', False):
                counts[key]['correct'] += 1
    
    if not counts:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No correctness data available",
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title("Correctness")
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scenarios = sorted(set(k[0] for k in counts.keys()))
    modes = sorted(set(k[1] for k in counts.keys()))
    
    x_pos = np.arange(len(scenarios))
    width = 0.35
    
    for i, mode in enumerate(modes):
        percentages = []
        for scenario in scenarios:
            key = (scenario, mode)
            if key in counts:
                pct = 100 * counts[key]['correct'] / counts[key]['total']
            else:
                pct = 0
            percentages.append(pct)
        
        ax.bar(x_pos + i * width, percentages, width, label=mode)
    
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Correctness %")
    ax.set_title("Correctness by Scenario and Mode")
    ax.set_xticks(x_pos + width / 2)
    ax.set_xticklabels(scenarios, rotation=45)
    ax.legend()
    ax.set_ylim(0, 105)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()


def generate_cache_reuse_chart(data: Union[List[Dict], 'pd.DataFrame'],
                              output_path: Union[str, Path]) -> None:
    """Generate cache hit rate across repeats for (scenario,budget)."""
    if not HAS_MATPLOTLIB:
        return
    
    # Calculate cache hit rates
    hit_rates = {}
    
    for row in data:
        if row.get('mode') != 'sqrt':  # Only sqrt mode uses cache
            continue
            
        scenario = row.get('scenario', 'unknown')
        budget = row.get('budget_nodes')
        key = (scenario, budget)
        
        if key not in hit_rates:
            hit_rates[key] = {'hits': 0, 'total': 0}
        
        hit_rates[key]['total'] += 1
        if row.get('from_cache', False):
            hit_rates[key]['hits'] += 1
    
    if not hit_rates:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No cache data available",
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title("Cache Hit Rate")
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    labels = []
    rates = []
    
    for (scenario, budget), stats in sorted(hit_rates.items()):
        rate = 100 * stats['hits'] / stats['total'] if stats['total'] > 0 else 0
        labels.append(f"{scenario}\nbudget={budget}")
        rates.append(rate)
    
    bars = ax.bar(range(len(labels)), rates)
    ax.set_xlabel("Scenario + Budget")
    ax.set_ylabel("Cache Hit Rate %")
    ax.set_title("Cache Reuse Rate")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45)
    ax.set_ylim(0, 105)
    
    # Add value labels on bars
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()


def generate_energy_chart(data: Union[List[Dict], 'pd.DataFrame'],
                         output_path: Union[str, Path]) -> None:
    """Generate energy_uj vs (mode,budget) per scenario."""
    if not HAS_MATPLOTLIB:
        return
    
    # Check if we have any energy data
    has_energy = any(
        row.get('energy_uj') not in [None, "NA", 0] 
        for row in data if isinstance(data, list)
    )
    
    if not has_energy:
        print("No energy data available - skipping energy chart")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    _plot_energy_by_scenario(data, ax)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()


def _plot_memory_by_scenario(data: Union[List[Dict], 'pd.DataFrame'], 
                            memory_col: str, ax, ylabel: str) -> None:
    """Helper to plot memory metrics by scenario."""
    
    # Group data by scenario, mode, budget
    groups = {}
    for row in data:
        scenario = row.get('scenario', 'unknown')
        mode = row.get('mode', 'unknown')
        budget = row.get('budget_nodes', 'baseline')
        key = (scenario, mode, budget)
        
        if key not in groups:
            groups[key] = []
        
        # Convert bytes to MB
        memory_val = row.get(memory_col, 0)
        if isinstance(memory_val, (int, float)) and memory_val > 0:
            memory_mb = memory_val / (1024 * 1024)
        else:
            memory_mb = 0
        groups[key].append(memory_mb)
    
    scenarios = sorted(set(k[0] for k in groups.keys()))
    x_labels = []
    x_pos = 0
    x_ticks = []
    
    for scenario in scenarios:
        scenario_groups = {k: v for k, v in groups.items() if k[0] == scenario}
        
        if not scenario_groups:
            continue
            
        # Sort by mode and budget
        sorted_keys = sorted(scenario_groups.keys(), key=lambda x: (x[1], x[2] if x[2] != 'baseline' else -1))
        
        for i, key in enumerate(sorted_keys):
            values = scenario_groups[key]
            if values:
                mean_val = sum(values) / len(values)
                label = f"{key[1]}"
                if key[2] != 'baseline' and key[2] is not None:
                    label += f"-{key[2]}"
                
                ax.bar(x_pos, mean_val, label=label if scenario == scenarios[0] else "")
                x_labels.append(label)
                x_ticks.append(x_pos)
                x_pos += 1
        
        x_pos += 0.5  # Gap between scenarios
    
    ax.set_xlabel("Mode-Budget by Scenario")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{ylabel} by Scenario and Mode")
    if x_ticks:
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=45)
    if len(scenarios) > 1:
        ax.legend()


def _plot_energy_by_scenario(data: Union[List[Dict], 'pd.DataFrame'], ax) -> None:
    """Helper to plot energy metrics by scenario.""" 
    
    # Similar to memory plotting but for energy
    groups = {}
    for row in data:
        energy_val = row.get('energy_uj')
        if energy_val in [None, "NA"]:
            continue
            
        scenario = row.get('scenario', 'unknown')
        mode = row.get('mode', 'unknown')
        budget = row.get('budget_nodes', 'baseline')
        key = (scenario, mode, budget)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(float(energy_val))
    
    if not groups:
        ax.text(0.5, 0.5, "No energy data available",
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title("Energy vs Mode")
        return
    
    # Plot similar to memory
    x_pos = 0
    x_ticks = []
    x_labels = []
    
    scenarios = sorted(set(k[0] for k in groups.keys()))
    
    for scenario in scenarios:
        scenario_groups = {k: v for k, v in groups.items() if k[0] == scenario}
        sorted_keys = sorted(scenario_groups.keys(), key=lambda x: (x[1], x[2] if x[2] != 'baseline' else -1))
        
        for key in sorted_keys:
            values = scenario_groups[key]
            if values:
                mean_val = sum(values) / len(values)
                label = f"{key[1]}"
                if key[2] != 'baseline' and key[2] is not None:
                    label += f"-{key[2]}"
                
                ax.bar(x_pos, mean_val / 1000000, label=label if scenario == scenarios[0] else "")  # Convert to Joules
                x_labels.append(label)
                x_ticks.append(x_pos)
                x_pos += 1
        x_pos += 0.5
    
    ax.set_xlabel("Mode-Budget by Scenario")
    ax.set_ylabel("Energy (J)")
    ax.set_title("Energy Consumption by Scenario and Mode")
    if x_ticks:
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=45)
    if len(scenarios) > 1:
        ax.legend()


def _calculate_slowdowns(data: Union[List[Dict], 'pd.DataFrame']) -> List[Dict[str, Any]]:
    """Calculate slowdown factors (sqrt_time / baseline_time) by scenario and budget."""
    
    # Group by scenario and budget, calculate medians
    baseline_times = {}  # scenario -> median_time
    sqrt_times = {}      # (scenario, budget) -> median_time
    
    for row in data:
        scenario = row.get('scenario', 'unknown')
        mode = row.get('mode', 'unknown')
        wall_s = row.get('wall_s', 0)
        
        if wall_s <= 0:
            continue
            
        if mode == 'baseline':
            if scenario not in baseline_times:
                baseline_times[scenario] = []
            baseline_times[scenario].append(wall_s)
        elif mode == 'sqrt':
            budget = row.get('budget_nodes')
            key = (scenario, budget)
            if key not in sqrt_times:
                sqrt_times[key] = []
            sqrt_times[key].append(wall_s)
    
    # Calculate medians
    baseline_medians = {}
    for scenario, times in baseline_times.items():
        times_sorted = sorted(times)
        n = len(times_sorted)
        if n > 0:
            if n % 2 == 1:
                baseline_medians[scenario] = times_sorted[n // 2]
            else:
                baseline_medians[scenario] = (times_sorted[n//2 - 1] + times_sorted[n//2]) / 2
    
    sqrt_medians = {}
    for key, times in sqrt_times.items():
        times_sorted = sorted(times)
        n = len(times_sorted)
        if n > 0:
            if n % 2 == 1:
                sqrt_medians[key] = times_sorted[n // 2]
            else:
                sqrt_medians[key] = (times_sorted[n//2 - 1] + times_sorted[n//2]) / 2
    
    # Calculate slowdown factors
    slowdowns = []
    for (scenario, budget), sqrt_median in sqrt_medians.items():
        if scenario in baseline_medians:
            baseline_median = baseline_medians[scenario]
            if baseline_median > 0:
                slowdown_factor = sqrt_median / baseline_median
                slowdowns.append({
                    'scenario': scenario,
                    'budget': budget,
                    'slowdown_factor': slowdown_factor,
                    'sqrt_time': sqrt_median,
                    'baseline_time': baseline_median
                })
    
    return slowdowns