"""
Test memory tracking improvements for benchmarking.

Validates that the enhanced memory tracking and payload systems work correctly.
"""

import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_memory_tracking_shows_differences():
    """Test that memory tracking now shows real differences with payloads."""
    from bench.run_suite import main
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run with payloads to create memory pressure
        exit_code = main([
            '--scenarios', 'tiny', 
            '--payload-bytes', '1048576',  # 1MB payloads
            '--outdir', tmpdir,
            '--repeats', '2'
        ])
        
        assert exit_code == 0, "Benchmark should complete successfully"
        
        # Read results and verify memory measurements are non-zero
        results_file = Path(tmpdir) / "results.csv"
        assert results_file.exists(), "Results file should be created"
        
        with open(results_file, 'r') as f:
            lines = f.readlines()
        
        # Check that some delta_rss_bytes values are > 0 (column 5, 0-indexed)
        delta_rss_values = []
        for i, line in enumerate(lines[1:]):  # Skip header
            cols = line.strip().split(',')
            if len(cols) > 4:
                delta_rss = int(cols[4])
                delta_rss_values.append(delta_rss)
        
        # At least some runs should show non-zero memory delta 
        non_zero_deltas = sum(1 for d in delta_rss_values if d > 0)
        assert non_zero_deltas > 0, f"Should have some non-zero memory deltas, got: {delta_rss_values[:10]}"
        
        print(f"✓ Memory tracking working: {non_zero_deltas}/{len(delta_rss_values)} runs show memory usage")


def test_clear_cache_functionality():
    """Test that clear cache functionality works."""
    from bench.run_suite import main
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run with clear cache option
        exit_code = main([
            '--scenarios', 'tiny',
            '--clear-plan-cache',
            '--outdir', tmpdir,
            '--repeats', '1'
        ])
        
        assert exit_code == 0, "Benchmark with clear cache should complete successfully"
        print("✓ Clear cache functionality works")


def test_memory_stress_scenario():
    """Test that memory stress scenario works and creates substantial usage."""
    from bench.run_suite import main
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run memory stress scenario 
        exit_code = main([
            '--scenarios', 'memory-stress',
            '--memory-stress-mb', '4',  # 4MB payloads
            '--outdir', tmpdir,
            '--repeats', '1'
        ])
        
        assert exit_code == 0, "Memory stress scenario should complete successfully"
        
        # Check that peak RSS is substantially higher than baseline
        results_file = Path(tmpdir) / "results.csv"
        with open(results_file, 'r') as f:
            lines = f.readlines()
        
        peak_rss_values = []
        for line in lines[1:]:  # Skip header
            cols = line.strip().split(',')
            if len(cols) > 12:  # peak_rss_bytes is column 13 (0-indexed = 12)
                peak_rss = int(cols[12])
                peak_rss_values.append(peak_rss)
        
        if peak_rss_values:
            avg_peak_mb = sum(peak_rss_values) / len(peak_rss_values) / (1024 * 1024)
            assert avg_peak_mb > 10, f"Memory stress should use >10MB, got {avg_peak_mb:.1f}MB"
            print(f"✓ Memory stress scenario creates substantial usage: {avg_peak_mb:.1f}MB average peak")


if __name__ == "__main__":
    test_memory_tracking_shows_differences()
    test_clear_cache_functionality() 
    test_memory_stress_scenario()
    print("All memory improvement tests passed! ✅")