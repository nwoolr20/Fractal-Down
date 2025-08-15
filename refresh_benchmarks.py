#!/usr/bin/env python3
"""
Script to remove old artifacts and generate fresh benchmark results.

This script:
1. Removes all old benchmark artifacts from the artifacts/ directory
2. Clears all cached plan files 
3. Generates fresh benchmark results with a reasonable default configuration
"""

import sys
import shutil
from pathlib import Path

# Add the project root to the path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from fractal_down.cache import clear_cache
from bench.run_suite import main as bench_main


def main():
    """Remove old artifacts and generate fresh benchmark results."""
    print("🗑️  Removing old artifacts and generating fresh benchmark results...")
    
    # Remove old artifacts
    artifacts_dir = repo_root / "artifacts"
    if artifacts_dir.exists():
        print(f"Removing old artifacts from {artifacts_dir}")
        shutil.rmtree(artifacts_dir)
        artifacts_dir.mkdir(exist_ok=True)
    else:
        print("No artifacts directory found, creating new one")
        artifacts_dir.mkdir(exist_ok=True)
    
    # Clear cached plan files
    print("Clearing cached plan files...")
    clear_cache()
    
    # Generate fresh benchmark results with reasonable defaults
    print("Generating fresh benchmark results...")
    exit_code = bench_main([
        '--scenarios', 'tiny', 
        '--repeats', '5',
        '--budgets', '2,3,4,5'
    ])
    
    if exit_code == 0:
        print("✅ Fresh benchmark results generated successfully!")
        
        # List the new results
        new_dirs = list(artifacts_dir.glob("*"))
        if new_dirs:
            latest_dir = max(new_dirs, key=lambda p: p.stat().st_mtime)
            print(f"📊 Results available in: {latest_dir}")
            
            # Show what was generated
            result_files = list(latest_dir.glob("*"))
            print("Generated files:")
            for f in sorted(result_files):
                print(f"  - {f.name}")
        else:
            print("⚠️  No results directory found")
    else:
        print("❌ Benchmark generation failed!")
        return exit_code
    
    return 0


if __name__ == "__main__":
    sys.exit(main())