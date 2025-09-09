# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Data persistence for benchmark results.

Handles creating timestamped run directories and saving CSV/JSON results.
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union


def new_run_dir(prefix: str = "bench") -> Path:
    """
    Create a new timestamped run directory.
    
    Args:
        prefix: Prefix for the directory name
        
    Returns:
        Path to the created directory
    """
    # Get repository root (parent of this file's directory)
    repo_root = Path(__file__).parent.parent
    artifacts_dir = repo_root / "artifacts"
    
    # Create artifacts directory if it doesn't exist
    artifacts_dir.mkdir(exist_ok=True)
    
    # Generate timestamped directory name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = artifacts_dir / f"{timestamp}_{prefix}"
    
    # Create the run directory
    run_dir.mkdir(exist_ok=True)
    
    return run_dir


def write_json(obj: Any, path: Union[str, Path]) -> None:
    """
    Write an object to a JSON file.
    
    Args:
        obj: Object to serialize to JSON
        path: Path to write the JSON file
    """
    path = Path(path)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, default=_json_serializer)


def write_csv(rows: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """
    Write rows to a CSV file with sorted column headers.
    
    Args:
        rows: List of dictionaries to write as CSV rows
        path: Path to write the CSV file
    """
    if not rows:
        return
    
    path = Path(path)
    
    # Get all unique column names and sort them
    columns = set()
    for row in rows:
        columns.update(row.keys())
    sorted_columns = sorted(columns)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_columns)
        writer.writeheader()
        writer.writerows(rows)


def _json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for types that aren't normally serializable.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serializable representation
    """
    if isinstance(obj, Path):
        return str(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)