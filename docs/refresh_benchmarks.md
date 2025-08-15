# Refresh Benchmarks

This script (`refresh_benchmarks.py`) provides an automated way to remove old artifacts and generate fresh benchmark results.

## Usage

```bash
python refresh_benchmarks.py
```

## What it does

1. **Removes old artifacts**: Clears the entire `artifacts/` directory of old benchmark runs
2. **Clears plan cache**: Removes all cached `.fplan` files to ensure fresh computation
3. **Generates fresh results**: Runs a new benchmark with sensible defaults:
   - Scenarios: `tiny` (lightweight for quick testing)
   - Repeats: 5 (good statistical sampling)
   - Budgets: 2, 3, 4, 5 (range of memory constraints)

## Output

The script generates a timestamped directory in `artifacts/` containing:
- `results.csv` - Raw benchmark data
- `summary.json` - Statistical summary
- `system.json` - System information
- `*.png` - Performance charts (slowdown, memory, correctness, cache reuse)

## Integration

This script can be used:
- During development to get clean benchmark baselines
- In CI/CD pipelines to generate fresh performance data
- Before performance comparisons to ensure clean starting state