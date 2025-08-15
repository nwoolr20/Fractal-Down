"""
Test that the requirements files are properly formatted and parseable.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_files_exist():
    """Test that all expected requirements files exist."""
    project_root = Path(__file__).parent.parent
    
    required_files = [
        "requirements.txt",
        "requirements-test.txt", 
        "requirements-bench.txt",
        "requirements-torch.txt",
        "requirements-dev.txt"
    ]
    
    for req_file in required_files:
        file_path = project_root / req_file
        assert file_path.exists(), f"Requirements file {req_file} does not exist"

def test_requirements_parseable():
    """Test that requirements files can be parsed by pip."""
    project_root = Path(__file__).parent.parent
    
    # Test that each requirements file can be parsed without errors
    for req_file in ["requirements-test.txt", "requirements-bench.txt", "requirements-torch.txt"]:
        file_path = project_root / req_file
        
        # Use pip-tools to dry-run parse the requirements
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                f"from pip._internal.req import parse_requirements; "
                f"from pip._internal.network.session import PipSession; "
                f"list(parse_requirements('{file_path}', session=PipSession()))"
            ], capture_output=True, text=True, cwd=project_root)
            
            assert result.returncode == 0, f"Failed to parse {req_file}: {result.stderr}"
            
        except Exception as e:
            assert False, f"Exception parsing {req_file}: {e}"

def test_dev_requirements_includes_all():
    """Test that dev requirements includes all other requirement files."""
    project_root = Path(__file__).parent.parent
    dev_req_path = project_root / "requirements-dev.txt"
    
    with open(dev_req_path) as f:
        dev_content = f.read()
    
    # Should include references to other requirement files
    assert "-r requirements-test.txt" in dev_content
    assert "-r requirements-bench.txt" in dev_content  
    assert "-r requirements-torch.txt" in dev_content

if __name__ == "__main__":
    test_requirements_files_exist()
    test_requirements_parseable() 
    test_dev_requirements_includes_all()
    print("All requirements file tests passed! ✅")