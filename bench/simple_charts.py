# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Simple chart generation without matplotlib dependency.
Creates text-based and HTML charts for benchmark visualization.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union

def generate_simple_charts(data: List[Dict[str, Any]], run_dir: Union[str, Path]) -> None:
    """
    Generate simple charts and save to run directory.
    
    Args:
        data: Benchmark results data (list of dicts)
        run_dir: Directory to save charts
    """
    run_dir = Path(run_dir)
    
    try:
        # Convert string values to appropriate types
        processed_data = []
        for row in data:
            processed_row = _process_row(row)
            processed_data.append(processed_row)
        
        generate_text_summary_chart(processed_data, run_dir / "summary_chart.txt")
        generate_html_charts(processed_data, run_dir / "charts.html")
        generate_csv_analysis(processed_data, run_dir / "analysis.csv")
        print(f"Simple charts and analysis saved to {run_dir}")
    except Exception as e:
        print(f"Error generating simple charts: {e}")
        import traceback
        traceback.print_exc()


def _process_row(row):
    """Convert string values from CSV to appropriate types."""
    processed = {}
    for key, value in row.items():
        if value == '' or value is None:
            processed[key] = None
        elif key in ['wall_s', 'cpu_s', 'recompute_factor']:
            try:
                processed[key] = float(value) if value != '' else 0.0
            except (ValueError, TypeError):
                processed[key] = 0.0
        elif key in ['peak_rss_bytes', 'peak_vram_bytes', 'pre_rss_bytes', 'delta_rss_bytes', 
                     'budget_nodes', 'order_len', 'unique_nodes', 'repeat', 'rss_cap_mb']:
            try:
                processed[key] = int(value) if value != '' else None
            except (ValueError, TypeError):
                processed[key] = None
        elif key in ['correct', 'from_cache', 'rss_cap_exceeded']:
            processed[key] = value.lower() == 'true' if isinstance(value, str) else bool(value)
        else:
            processed[key] = value
    return processed


def generate_text_summary_chart(data: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """Generate a text-based summary chart showing key metrics."""
    
    # Group data by scenario and mode
    groups = {}
    for row in data:
        scenario = row.get('scenario', 'unknown')
        mode = row.get('mode', 'unknown')
        budget = row.get('budget_nodes', 'baseline')
        key = (scenario, mode, budget)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    
    # Create text chart
    lines = []
    lines.append("=" * 80)
    lines.append("FRACTAL-DOWN BENCHMARK RESULTS - TEXT CHART")
    lines.append("=" * 80)
    lines.append("")
    
    scenarios = sorted(set(k[0] for k in groups.keys()))
    
    for scenario in scenarios:
        lines.append(f"SCENARIO: {scenario.upper()}")
        lines.append("-" * 50)
        
        scenario_groups = {k: v for k, v in groups.items() if k[0] == scenario}
        
        # Calculate baseline times for comparison
        baseline_times = []
        for key, group_data in scenario_groups.items():
            if key[1] == 'baseline':
                baseline_times.extend([r.get('wall_s', 0) for r in group_data if r.get('wall_s', 0) > 0])
        
        baseline_median = _calculate_median(baseline_times) if baseline_times else 0
        
        lines.append(f"{'Mode':<15} {'Budget':<8} {'Time(ms)':<12} {'Memory(MB)':<12} {'Slowdown':<10} {'Correct%':<10}")
        lines.append("-" * 75)
        
        for key in sorted(scenario_groups.keys(), key=lambda x: (x[1], x[2] if x[2] != 'baseline' else -1)):
            mode, budget = key[1], key[2]
            group_data = scenario_groups[key]
            
            # Calculate metrics
            times = [r.get('wall_s', 0) for r in group_data if r.get('wall_s', 0) > 0]
            memory_vals = [r.get('peak_rss_bytes', 0) for r in group_data if r.get('peak_rss_bytes', 0) > 0]
            correct_count = sum(1 for r in group_data if r.get('correct', False))
            total_count = len(group_data)
            
            if times:
                time_median = _calculate_median(times)
                time_ms = time_median * 1000
                slowdown = time_median / baseline_median if baseline_median > 0 else 1.0
            else:
                time_ms = 0
                slowdown = 1.0
            
            if memory_vals:
                memory_median = _calculate_median(memory_vals) / (1024 * 1024)  # Convert to MB
            else:
                memory_median = 0
            
            correct_pct = (correct_count / total_count * 100) if total_count > 0 else 0
            
            budget_str = str(budget) if budget != 'baseline' else '-'
            lines.append(f"{mode:<15} {budget_str:<8} {time_ms:<12.2f} {memory_median:<12.1f} {slowdown:<10.2f} {correct_pct:<10.1f}%")
        
        lines.append("")
        
        # Add memory usage bar chart
        lines.append("Memory Usage (MB) - Visual Bar Chart:")
        for key in sorted(scenario_groups.keys(), key=lambda x: (x[1], x[2] if x[2] != 'baseline' else -1)):
            mode, budget = key[1], key[2]
            group_data = scenario_groups[key]
            memory_vals = [r.get('peak_rss_bytes', 0) for r in group_data if r.get('peak_rss_bytes', 0) > 0]
            
            if memory_vals:
                memory_mb = _calculate_median(memory_vals) / (1024 * 1024)
                bar_length = int(memory_mb / 10)  # Scale: 1 char = 10MB
                bar = "█" * bar_length
                budget_str = f"-{budget}" if budget != 'baseline' else ""
                lines.append(f"  {mode}{budget_str:<12}: {bar} {memory_mb:.1f}MB")
        
        lines.append("")
        lines.append("")
    
    # Overall summary
    lines.append("OVERALL SUMMARY")
    lines.append("-" * 30)
    
    all_correct = sum(1 for r in data if r.get('correct', False))
    total_jobs = len([r for r in data if 'correct' in r])
    overall_correct = (all_correct / total_jobs * 100) if total_jobs > 0 else 0
    
    cache_jobs = [r for r in data if r.get('mode') == 'sqrt']
    cache_hits = sum(1 for r in cache_jobs if r.get('from_cache', False))
    cache_rate = (cache_hits / len(cache_jobs) * 100) if cache_jobs else 0
    
    lines.append(f"Total Jobs: {len(data)}")
    lines.append(f"Overall Correctness: {all_correct}/{total_jobs} ({overall_correct:.1f}%)")
    lines.append(f"Cache Hit Rate: {cache_hits}/{len(cache_jobs)} ({cache_rate:.1f}%)")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def generate_html_charts(data: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """Generate HTML-based charts with CSS styling."""
    
    # Prepare data
    groups = {}
    for row in data:
        scenario = row.get('scenario', 'unknown')
        mode = row.get('mode', 'unknown')
        budget = row.get('budget_nodes', 'baseline')
        key = (scenario, mode, budget)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Fractal-Down Benchmark Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; }
        .scenario { background: white; margin: 20px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .scenario h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .memory-bar { background: #e9ecef; height: 20px; border-radius: 10px; margin: 2px 0; position: relative; }
        .memory-fill { background: linear-gradient(90deg, #4CAF50, #45a049); height: 100%; border-radius: 10px; }
        .memory-text { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); font-size: 12px; color: white; text-shadow: 1px 1px 1px rgba(0,0,0,0.5); }
        .slowdown-good { color: #4CAF50; font-weight: bold; }
        .slowdown-warning { color: #FF9800; font-weight: bold; }
        .slowdown-bad { color: #f44336; font-weight: bold; }
        .correct-good { color: #4CAF50; font-weight: bold; }
        .correct-bad { color: #f44336; font-weight: bold; }
        .summary { background: white; padding: 15px; border-radius: 8px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Fractal-Down Benchmark Results</h1>
        <p>DAG evaluation with √N memory and fractal priority scheduling</p>
    </div>
"""
    
    scenarios = sorted(set(k[0] for k in groups.keys()))
    max_memory = max([r.get('peak_rss_bytes', 0) for r in data]) / (1024 * 1024)  # Max memory in MB
    
    for scenario in scenarios:
        html_content += f'    <div class="scenario">\n        <h2>📊 Scenario: {scenario.upper()}</h2>\n'
        
        scenario_groups = {k: v for k, v in groups.items() if k[0] == scenario}
        
        # Calculate baseline for slowdown comparison
        baseline_times = []
        for key, group_data in scenario_groups.items():
            if key[1] == 'baseline':
                baseline_times.extend([r.get('wall_s', 0) for r in group_data if r.get('wall_s', 0) > 0])
        baseline_median = _calculate_median(baseline_times) if baseline_times else 0
        
        html_content += """        <table>
            <thead>
                <tr>
                    <th>Mode</th>
                    <th>Budget</th>
                    <th>Time (ms)</th>
                    <th>Memory Usage</th>
                    <th>Slowdown</th>
                    <th>Correctness</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for key in sorted(scenario_groups.keys(), key=lambda x: (x[1], x[2] if x[2] != 'baseline' else -1)):
            mode, budget = key[1], key[2]
            group_data = scenario_groups[key]
            
            # Calculate metrics
            times = [r.get('wall_s', 0) for r in group_data if r.get('wall_s', 0) > 0]
            memory_vals = [r.get('peak_rss_bytes', 0) for r in group_data if r.get('peak_rss_bytes', 0) > 0]
            correct_count = sum(1 for r in group_data if r.get('correct', False))
            total_count = len(group_data)
            
            if times:
                time_median = _calculate_median(times)
                time_ms = time_median * 1000
                slowdown = time_median / baseline_median if baseline_median > 0 else 1.0
            else:
                time_ms = 0
                slowdown = 1.0
            
            if memory_vals:
                memory_median = _calculate_median(memory_vals) / (1024 * 1024)  # Convert to MB
                memory_pct = (memory_median / max_memory * 100) if max_memory > 0 else 0
            else:
                memory_median = 0
                memory_pct = 0
            
            correct_pct = (correct_count / total_count * 100) if total_count > 0 else 0
            
            # Styling based on values
            slowdown_class = "slowdown-good" if slowdown <= 1.2 else ("slowdown-warning" if slowdown <= 2.0 else "slowdown-bad")
            correct_class = "correct-good" if correct_pct >= 95 else "correct-bad"
            
            budget_str = str(budget) if budget != 'baseline' else '-'
            
            html_content += f"""                <tr>
                    <td>{mode}</td>
                    <td>{budget_str}</td>
                    <td>{time_ms:.2f}</td>
                    <td>
                        <div class="memory-bar">
                            <div class="memory-fill" style="width: {memory_pct:.1f}%"></div>
                            <div class="memory-text">{memory_median:.1f} MB</div>
                        </div>
                    </td>
                    <td class="{slowdown_class}">{slowdown:.2f}x</td>
                    <td class="{correct_class}">{correct_pct:.1f}%</td>
                </tr>
"""
        
        html_content += """            </tbody>
        </table>
    </div>
"""
    
    # Overall summary
    all_correct = sum(1 for r in data if r.get('correct', False))
    total_jobs = len([r for r in data if 'correct' in r])
    overall_correct = (all_correct / total_jobs * 100) if total_jobs > 0 else 0
    
    cache_jobs = [r for r in data if r.get('mode') == 'sqrt']
    cache_hits = sum(1 for r in cache_jobs if r.get('from_cache', False))
    cache_rate = (cache_hits / len(cache_jobs) * 100) if cache_jobs else 0
    
    html_content += f"""    <div class="summary">
        <h2>📈 Overall Summary</h2>
        <p><strong>Total Jobs:</strong> {len(data)}</p>
        <p><strong>Overall Correctness:</strong> {all_correct}/{total_jobs} ({overall_correct:.1f}%)</p>
        <p><strong>Cache Hit Rate:</strong> {cache_hits}/{len(cache_jobs)} ({cache_rate:.1f}%)</p>
        <p><strong>Average Memory Usage:</strong> {sum(r.get('peak_rss_bytes', 0) for r in data) / len(data) / (1024*1024):.1f} MB</p>
    </div>

</body>
</html>"""
    
    with open(output_path, 'w') as f:
        f.write(html_content)


def generate_csv_analysis(data: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """Generate a CSV with analyzed/aggregated results."""
    
    # Group data and calculate statistics
    groups = {}
    for row in data:
        scenario = row.get('scenario', 'unknown')
        mode = row.get('mode', 'unknown')
        budget = row.get('budget_nodes', 'baseline')
        key = (scenario, mode, budget)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    
    # Write analysis CSV
    lines = ["scenario,mode,budget,jobs_count,time_median_ms,time_std_ms,memory_median_mb,memory_std_mb,correctness_pct,cache_hit_pct,recompute_factor_avg"]
    
    for key, group_data in sorted(groups.items()):
        scenario, mode, budget = key
        
        # Time statistics
        times = [r.get('wall_s', 0) for r in group_data if r.get('wall_s', 0) > 0]
        time_median = _calculate_median(times) * 1000 if times else 0  # Convert to ms
        time_std = _calculate_std(times) * 1000 if len(times) > 1 else 0
        
        # Memory statistics  
        memory_vals = [r.get('peak_rss_bytes', 0) for r in group_data if r.get('peak_rss_bytes', 0) > 0]
        memory_median = _calculate_median(memory_vals) / (1024 * 1024) if memory_vals else 0  # Convert to MB
        memory_std = _calculate_std(memory_vals) / (1024 * 1024) if len(memory_vals) > 1 else 0
        
        # Correctness
        correct_count = sum(1 for r in group_data if r.get('correct', False))
        correctness_pct = (correct_count / len(group_data) * 100) if group_data else 0
        
        # Cache hit rate (only for sqrt mode)
        if mode == 'sqrt':
            cache_hits = sum(1 for r in group_data if r.get('from_cache', False))
            cache_hit_pct = (cache_hits / len(group_data) * 100) if group_data else 0
        else:
            cache_hit_pct = 0
        
        # Recompute factor
        recompute_factors = [r.get('recompute_factor', 1.0) for r in group_data if r.get('recompute_factor') is not None]
        recompute_factor_avg = sum(recompute_factors) / len(recompute_factors) if recompute_factors else 1.0
        
        budget_str = str(budget) if budget != 'baseline' else ''
        
        lines.append(f"{scenario},{mode},{budget_str},{len(group_data)},{time_median:.2f},{time_std:.2f},{memory_median:.1f},{memory_std:.1f},{correctness_pct:.1f},{cache_hit_pct:.1f},{recompute_factor_avg:.2f}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def _calculate_median(values):
    """Calculate median of a list of numbers."""
    if not values:
        return 0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 1:
        return sorted_values[n // 2]
    else:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2


def _calculate_std(values):
    """Calculate standard deviation of a list of numbers."""
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5