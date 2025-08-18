"""
Test that the requirements files are properly formatted and parseable.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_files_exist():
    """Test that the main requirements file exists."""
    project_root = Path(__file__).parent.parent
    
    # Only check for the main requirements.txt file
    req_file = "requirements.txt"
    file_path = project_root / req_file
    assert file_path.exists(), f"Requirements file {req_file} does not exist"

def test_requirements_parseable():
    """Test that the main requirements file can be parsed by pip."""
    project_root = Path(__file__).parent.parent
    
    # Test that requirements.txt can be parsed without errors
    file_path = project_root / "requirements.txt"
    
    # Use pip-tools to dry-run parse the requirements
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            f"from pip._internal.req import parse_requirements; "
            f"from pip._internal.network.session import PipSession; "
            f"list(parse_requirements('{file_path}', session=PipSession()))"
        ], capture_output=True, text=True, cwd=project_root)
        
        assert result.returncode == 0, f"Failed to parse requirements.txt: {result.stderr}"
        
    except Exception as e:
        assert False, f"Exception parsing requirements.txt: {e}"

def test_main_requirements_includes_all():
    """Test that the main requirements file includes all optional dependencies via pyproject.toml."""
    project_root = Path(__file__).parent.parent
    req_path = project_root / "requirements.txt"
    
    with open(req_path) as f:
        content = f.read()
    
    # Should include reference to pyproject.toml with all extras
    assert "-e .[test,bench,torch]" in content

if __name__ == "__main__":
    test_requirements_files_exist()
    test_requirements_parseable() 
    test_main_requirements_includes_all()
    print("All requirements file tests passed! ✅")