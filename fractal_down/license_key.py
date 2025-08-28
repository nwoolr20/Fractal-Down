"""Simple license key and contract tracking for Fractal-Down.

This module provides minimal utilities for issuing and verifying
license keys. License data is stored in a JSON file on disk and can
optionally be redirected via the ``FRACTAL_DOWN_LICENSE_FILE``
environment variable.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import List


# Resolve license file path, allowing override through environment variable.
DEFAULT_PATH = Path.home() / ".fractal_down" / "licenses.json"
LICENSE_FILE = Path(os.environ.get("FRACTAL_DOWN_LICENSE_FILE", DEFAULT_PATH))


@dataclass
class LicenseRecord:
    """A stored license key tied to a contract identifier."""

    key: str
    contract: str


def _ensure_storage() -> None:
    """Ensure the storage directory exists."""
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_licenses() -> List[dict]:
    """Load all license records from disk."""
    if not LICENSE_FILE.exists():
        return []
    with LICENSE_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_licenses(records: List[dict]) -> None:
    """Persist license records to disk."""
    _ensure_storage()
    with LICENSE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def generate_license(contract: str) -> LicenseRecord:
    """Generate and store a new license key for ``contract``.

    Returns the generated :class:`LicenseRecord`.
    """
    records = load_licenses()
    key = secrets.token_hex(16)
    record = {"key": key, "contract": contract}
    records.append(record)
    save_licenses(records)
    return LicenseRecord(key=key, contract=contract)


def verify_license(key: str) -> bool:
    """Check whether ``key`` exists in stored licenses."""
    return any(rec.get("key") == key for rec in load_licenses())
