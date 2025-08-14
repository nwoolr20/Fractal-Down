"""
Smoke test for benchmark suite.

Tests that the benchmark suite can run without errors and produces expected outputs.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import matplotlib
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@pytest.mark.skipif(not (HAS_PSUTIL and HAS_MATPLOTLIB), 
                   reason="psutil and matplotlib required for benchmark suite")
def test_bench_smoke():
    """Run minimal benchmark suite and verify outputs are created."""
    
    import bench.run_suite
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        outdir = Path(tmpdir) / "bench_test"
        outdir.mkdir()
        
        # Run tiny scenario only with minimal settings
        args = [
            '--scenarios', 'tiny',
            '--repeats', '1', 
            '--budgets', '2,3',
            '--verify',
            '--outdir', str(outdir)
        ]
        
        # Run benchmark
        result = bench.run_suite.main(args)
        
        # Should complete successfully
        assert result == 0
        
        # Check that expected files were created
        assert (outdir / "system.json").exists()
        assert (outdir / "results.csv").exists()
        assert (outdir / "summary.json").exists()
        
        # Check that at least some charts were created
        chart_files = list(outdir.glob("*.png"))
        assert len(chart_files) >= 2, f"Expected at least 2 PNG files, found: {[f.name for f in chart_files]}"
        
        # Verify results.csv has expected structure
        with open(outdir / "results.csv", 'r') as f:
            header = f.readline().strip()
            expected_columns = [
                'budget_nodes', 'correct', 'cpu_s', 'energy_uj', 'from_cache', 
                'job', 'mode', 'notes', 'peak_rss_bytes', 'peak_vram_bytes', 
                'repeat', 'scenario', 'wall_s'
            ]
            for col in expected_columns:
                assert col in header, f"Expected column '{col}' not found in CSV header"


def test_bench_system_info():
    """Test that system info collection works."""
    from bench.system_info import collect_system_info
    
    info = collect_system_info()
    
    # Check required fields are present
    required_fields = [
        'os', 'python_version', 'cpu_model', 'logical_cores',
        'physical_cores', 'ram_total_gb', 'gpu_models', 'gpu_count', 
        'cuda_available', 'torch_version'
    ]
    
    for field in required_fields:
        assert field in info, f"Missing field: {field}"
    
    # Basic sanity checks
    assert isinstance(info['logical_cores'], (int, str))
    assert info['os'] in ['Linux', 'Windows', 'Darwin'] or info['os'] != ''


def test_bench_scenarios():
    """Test that scenario generation works."""
    from bench.scenarios import scenario_tiny, scenario_synthetic
    
    # Test tiny scenario
    tiny_jobs = scenario_tiny()
    assert len(tiny_jobs) > 0
    
    # Should have both baseline and sqrt jobs
    modes = set(job.mode for job in tiny_jobs)
    assert 'baseline' in modes
    assert 'sqrt' in modes
    
    # Test synthetic scenario  
    synthetic_jobs = scenario_synthetic(50)  # Small size for testing
    assert len(synthetic_jobs) > 0
    
    modes = set(job.mode for job in synthetic_jobs)
    assert 'baseline' in modes
    assert 'sqrt' in modes


@pytest.mark.skipif(not HAS_PSUTIL, reason="psutil required for metrics")
def test_bench_metrics():
    """Test that metrics collection works."""
    from bench.metrics import track_peak_rss, Timer, measure_vram_peak, measure_energy, check_correctness
    import time
    
    # Test RSS tracking
    with track_peak_rss() as rss_ctx:
        # Do some memory allocation
        data = [i for i in range(10000)]
        time.sleep(0.1)
    
    assert 'peak_rss_bytes' in rss_ctx
    assert rss_ctx['peak_rss_bytes'] >= 0
    
    # Test timing
    with Timer() as timer_ctx:
        time.sleep(0.1)
    
    assert 'wall_s' in timer_ctx
    assert 'cpu_s' in timer_ctx
    assert timer_ctx['wall_s'] >= 0.05  # Should be at least ~0.1s
    
    # Test VRAM (may not be available)
    with measure_vram_peak() as vram_ctx:
        pass
    
    assert 'peak_vram_bytes' in vram_ctx
    assert vram_ctx['peak_vram_bytes'] >= 0
    
    # Test energy (may not be available)
    with measure_energy() as energy_ctx:
        pass
    
    assert 'energy_uj' in energy_ctx
    # energy_uj may be "NA" if not supported
    
    # Test correctness check
    assert check_correctness(b'test', b'test') == True
    assert check_correctness(b'test', b'other') == False